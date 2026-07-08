from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=30)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_playbook_revision_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "forecast_error_watch_ratio": d("0.080000"),
        "forecast_error_block_ratio": d("0.200000"),
        "stale_memory_reuse_watch_ratio": d("0.150000"),
        "stale_memory_reuse_block_ratio": d("0.350000"),
        "correction_gap_watch_ratio": d("0.250000"),
        "correction_gap_block_ratio": d("0.500000"),
        "evidence_gap_watch_ratio": d("0.250000"),
        "evidence_gap_block_ratio": d("0.500000"),
        "peer_review_depth_gap_watch_ratio": d("0.250000"),
        "peer_review_depth_gap_block_ratio": d("0.500000"),
        "review_latency_watch_seconds": d("3600.000000"),
        "review_latency_block_seconds": d("7200.000000"),
        "forecast_error_weight": d("0.250000"),
        "stale_memory_reuse_weight": d("0.150000"),
        "correction_follow_through_weight": d("0.200000"),
        "evidence_coverage_weight": d("0.150000"),
        "peer_review_depth_weight": d("0.100000"),
        "review_latency_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistPlaybookRevisionQueueConfig(**values)


def revision_signal(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "revision_ref": "revision-alpha",
        "specialist_ref": "specialist-alpha",
        "playbook_ref": "playbook-alpha",
        "observed_at": OBSERVED_AT,
        "forecast_error_attribution": d("0.030000"),
        "stale_memory_reuse_ratio": d("0.040000"),
        "correction_required_count": d("2"),
        "correction_completed_count": d("2"),
        "required_evidence_count": d("4"),
        "covered_evidence_count": d("4"),
        "required_peer_review_count": d("3"),
        "completed_peer_review_count": d("3"),
        "review_due_at": GENERATED_AT - timedelta(seconds=300),
        "reviewed_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistPlaybookRevisionQueueInput(**values)


def build_report(*signals: object, generated_at: datetime = GENERATED_AT, cfg: object | None = None):
    module = api()
    return module.build_research_team_specialist_playbook_revision_queue_report(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_decimal_only_numerics(value: Any) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"unexpected non-Decimal numeric value: {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_decimal_only_numerics(item)


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_int_or_float_values(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_int_or_float_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if type(value) is dict:
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if type(value) is list:
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_prioritizes_playbook_revisions_from_forecast_memory_correction_evidence_peer_and_latency_signals() -> None:
    module = api()

    report = build_report(
        revision_signal(
            revision_ref="revision-pass",
            specialist_ref="specialist-pass",
            playbook_ref="playbook-pass",
        ),
        revision_signal(
            revision_ref="revision-block",
            specialist_ref="specialist-block",
            playbook_ref="playbook-block",
            forecast_error_attribution=d("0.260000"),
            stale_memory_reuse_ratio=d("0.500000"),
            correction_required_count=d("4"),
            correction_completed_count=d("1"),
            required_evidence_count=d("4"),
            covered_evidence_count=d("1"),
            required_peer_review_count=d("4"),
            completed_peer_review_count=d("1"),
            review_due_at=GENERATED_AT - timedelta(seconds=8_000),
            reviewed_at=GENERATED_AT,
        ),
        revision_signal(
            revision_ref="revision-watch",
            specialist_ref="specialist-watch",
            playbook_ref="playbook-watch",
            forecast_error_attribution=d("0.120000"),
            stale_memory_reuse_ratio=d("0.200000"),
            correction_required_count=d("4"),
            correction_completed_count=d("3"),
            required_evidence_count=d("4"),
            covered_evidence_count=d("3"),
            required_peer_review_count=d("4"),
            completed_peer_review_count=d("3"),
            review_due_at=GENERATED_AT - timedelta(seconds=4_000),
            reviewed_at=GENERATED_AT,
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_REPORT_CONFIG_VERSION
    )
    assert module.RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.revision_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.forecast_error_flag_count == d("2")
    assert report.stale_memory_reuse_flag_count == d("2")
    assert report.correction_gap_count == d("2")
    assert report.evidence_gap_count == d("2")
    assert report.peer_review_depth_gap_count == d("2")
    assert report.review_latency_flag_count == d("2")
    assert report.max_priority_score == d("0.627500")
    assert report.average_priority_score == d("0.301028")
    assert report.max_review_latency_seconds == d("8000.000000")
    assert report.status == "block"
    assert report.paper_queue_action == "paper_playbook_revision_block"
    assert report.reason_codes == (
        "playbook_revision_queue_block",
        "forecast_error_attribution_block",
        "stale_memory_reuse_block",
        "correction_follow_through_block",
        "evidence_coverage_block",
        "peer_review_depth_block",
        "review_latency_block",
        "forecast_error_attribution_watch",
        "stale_memory_reuse_watch",
        "correction_follow_through_watch",
        "evidence_coverage_watch",
        "peer_review_depth_watch",
        "review_latency_watch",
    )

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.priority_score == d("0.627500")
    assert blocked.reason_codes == (
        "forecast_error_attribution_block",
        "stale_memory_reuse_block",
        "correction_follow_through_block",
        "evidence_coverage_block",
        "peer_review_depth_block",
        "review_latency_block",
    )
    assert watched.priority_score == d("0.255833")
    assert watched.reason_codes == (
        "forecast_error_attribution_watch",
        "stale_memory_reuse_watch",
        "correction_follow_through_watch",
        "evidence_coverage_watch",
        "peer_review_depth_watch",
        "review_latency_watch",
    )
    assert passed.priority_score == d("0.019750")
    assert passed.reason_codes == ("playbook_revision_clear",)
    assert all(row.revision_ref_digest.startswith("sha256:") for row in report.rows)
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_only_numerics(report)


def test_empty_queue_passes_with_hard_flags_and_no_rows() -> None:
    module = api()

    report = build_report()

    assert report.status == "pass"
    assert report.paper_queue_action == "paper_playbook_revision_monitor"
    assert report.revision_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.max_priority_score == d("0.000000")
    assert report.average_priority_score == d("0.000000")
    assert report.max_review_latency_seconds == d("0.000000")
    assert report.reason_codes == ("playbook_revision_queue_empty",)
    assert report.reason_code_counts == (
        module.ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount(
            reason_code="playbook_revision_queue_empty",
            count=d("1"),
            revision_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    for value in (report, *report.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
    assert_decimal_only_numerics(report)


def test_payload_is_deterministic_decimal_only_redacted_and_digest_checked() -> None:
    module = api()
    signal_a = revision_signal(
        revision_ref="revision-watch",
        specialist_ref="specialist-watch",
        playbook_ref="playbook-watch",
        forecast_error_attribution=d("0.120000"),
        stale_memory_reuse_ratio=d("0.200000"),
        correction_required_count=d("4"),
        correction_completed_count=d("3"),
        required_evidence_count=d("4"),
        covered_evidence_count=d("3"),
        required_peer_review_count=d("4"),
        completed_peer_review_count=d("3"),
        review_due_at=datetime(2026, 7, 8, 1, 53, 20, tzinfo=timezone(timedelta(hours=-7))),
        reviewed_at=datetime(2026, 7, 8, 3, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    signal_b = revision_signal(
        revision_ref="revision-pass",
        specialist_ref="specialist-pass",
        playbook_ref="playbook-pass",
    )

    report_a = build_report(
        signal_a,
        signal_b,
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    report_b = build_report(signal_b, signal_a)

    payload_a = module.research_team_specialist_playbook_revision_queue_report_payload(
        report_a,
    )
    payload_b = module.research_team_specialist_playbook_revision_queue_report_payload(
        report_b,
    )

    assert payload_a == payload_b
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["revision_count"] == "2"
    assert payload_a["rows"][0]["revision_ref_digest"] == (
        "sha256:" + sha256(b"revision-watch").hexdigest()
    )
    assert payload_a["rows"][0]["review_due_at"] == "2026-07-08T08:53:20+00:00"
    assert payload_a["rows"][0]["reviewed_at"] == "2026-07-08T10:00:00+00:00"
    assert payload_a["rows"][0]["review_latency_seconds"] == "4000.000000"
    assert payload_a["derived_validation_digest"] == report_a.derived_validation_digest
    assert_no_int_or_float_values(payload_a)
    json.dumps(payload_a, sort_keys=True)

    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload_a)
        for fragment in forbidden_fragments
    )
    payload_text = repr(payload_a).lower()
    assert "revision-watch" not in payload_text
    assert "specialist-watch" not in payload_text
    assert "playbook-watch" not in payload_text
    assert not any(fragment in payload_text for fragment in forbidden_fragments)

    tampered = dict(payload_a)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_playbook_revision_queue_report_payload(tampered)

    row_tampered = dict(payload_a)
    row_tampered["rows"] = [dict(payload_a["rows"][0]), dict(payload_a["rows"][1])]
    row_tampered["rows"][0]["priority_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_playbook_revision_queue_report_payload(row_tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, pass_count=d("2"))


def test_rejects_public_unsafe_surfaces_non_decimal_numbers_and_flag_downgrades() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        revision_signal(forecast_error_attribution=0.12)
    with pytest.raises(ValueError, match="Decimal"):
        revision_signal(forecast_error_attribution=_DecimalSubclass("0.120000"))
    with pytest.raises(ValueError, match="safe public"):
        revision_signal(revision_ref="market-slug-123")
    with pytest.raises(ValueError, match="must not be after generated_at"):
        build_report(revision_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(revision_signal(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        item = revision_signal()
        item.revision_ref = "other"  # type: ignore[misc]

    with pytest.raises(ValueError, match="weights must sum to 1"):
        config(review_latency_weight=d("0.140000"))
    with pytest.raises(ValueError, match="must exceed watch threshold"):
        config(forecast_error_block_ratio=d("0.080000"))

    payload = module.research_team_specialist_playbook_revision_queue_report_payload(
        build_report(revision_signal()),
    )
    for key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_specialist_playbook_revision_queue_report_payload(unsafe)

    for value in (
        "candidate raw value",
        "market slug",
        "https://example.test/path",
        "postgres://user:pass@example.test/db",
        "wallet route",
        "trade surface",
        "live endpoint",
    ):
        unsafe = dict(payload)
        unsafe["unsafe_value"] = value
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_specialist_playbook_revision_queue_report_payload(unsafe)

    unsafe_number = dict(payload)
    unsafe_number["revision_count"] = 1
    with pytest.raises(ValueError, match="string values"):
        module.research_team_specialist_playbook_revision_queue_report_payload(unsafe_number)
