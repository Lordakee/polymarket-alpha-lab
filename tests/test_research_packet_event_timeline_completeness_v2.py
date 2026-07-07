from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_event_timeline_completeness_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values = {
        "late_after_packet_grace_seconds": d("0.000000"),
    }
    values.update(overrides)
    return api().ResearchPacketEventTimelineCompletenessV2Config(**values)


def packet(
    packet_ref: str,
    *,
    team_id: str = "politics",
    category_id: str = "politics",
    packet_generated_at: datetime = GENERATED_AT - timedelta(hours=2),
    initial_catalyst_at: datetime | None = GENERATED_AT - timedelta(hours=6),
    primary_source_timestamp_at: datetime | None = GENERATED_AT - timedelta(hours=5),
    probability_move_timestamp_at: datetime | None = GENERATED_AT - timedelta(hours=4),
    follow_up_source_timestamp_at: datetime | None = GENERATED_AT - timedelta(hours=3),
    resolution_update_timestamp_at: datetime | None = GENERATED_AT - timedelta(hours=2, minutes=30),
    packet_config_version: str = "research-packet-test-v0",
):
    return api().ResearchPacketEventTimelineCompletenessV2Input(
        packet_ref=packet_ref,
        team_id=team_id,
        category_id=category_id,
        packet_generated_at=packet_generated_at,
        initial_catalyst_at=initial_catalyst_at,
        primary_source_timestamp_at=primary_source_timestamp_at,
        probability_move_timestamp_at=probability_move_timestamp_at,
        follow_up_source_timestamp_at=follow_up_source_timestamp_at,
        resolution_update_timestamp_at=resolution_update_timestamp_at,
        packet_config_version=packet_config_version,
    )


def report(*packets: object, **config_overrides: object):
    return api().build_research_packet_event_timeline_completeness_v2_report(
        packets,
        config=config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_report_scores_missing_and_late_event_timeline_steps_deterministically() -> None:
    module = api()

    timeline_report = report(
        packet(
            "packet-complete",
            team_id="sports_soccer",
            category_id="sports.soccer",
        ),
        packet(
            "packet-late",
            packet_generated_at=GENERATED_AT - timedelta(hours=3),
            follow_up_source_timestamp_at=GENERATED_AT - timedelta(hours=2),
            resolution_update_timestamp_at=GENERATED_AT - timedelta(hours=1),
        ),
        packet(
            "packet-missing",
            packet_generated_at=GENERATED_AT - timedelta(hours=1),
            primary_source_timestamp_at=None,
            probability_move_timestamp_at=GENERATED_AT - timedelta(minutes=30),
            resolution_update_timestamp_at=None,
        ),
    )
    repeated_report = report(
        packet(
            "packet-missing",
            packet_generated_at=GENERATED_AT - timedelta(hours=1),
            primary_source_timestamp_at=None,
            probability_move_timestamp_at=GENERATED_AT - timedelta(minutes=30),
            resolution_update_timestamp_at=None,
        ),
        packet(
            "packet-late",
            packet_generated_at=GENERATED_AT - timedelta(hours=3),
            follow_up_source_timestamp_at=GENERATED_AT - timedelta(hours=2),
            resolution_update_timestamp_at=GENERATED_AT - timedelta(hours=1),
        ),
        packet(
            "packet-complete",
            team_id="sports_soccer",
            category_id="sports.soccer",
        ),
    )

    assert is_dataclass(timeline_report)
    assert type(timeline_report) is module.ResearchPacketEventTimelineCompletenessV2Report
    assert timeline_report.generated_at == GENERATED_AT
    assert timeline_report.report_status == "blocked"
    assert timeline_report.source_packet_count == d("3")
    assert timeline_report.complete_packet_count == d("1")
    assert timeline_report.watch_packet_count == d("1")
    assert timeline_report.blocked_packet_count == d("1")
    assert timeline_report.required_step_count == d("15")
    assert timeline_report.complete_step_count == d("10")
    assert timeline_report.missing_step_count == d("2")
    assert timeline_report.late_step_count == d("3")
    assert timeline_report.completeness_ratio == d("0.666667")
    assert timeline_report.reason_codes == (
        "event_timeline_completeness_blocked",
        "event_timeline_missing_steps",
        "event_timeline_late_steps",
        "missing_primary_source_timestamp",
        "missing_resolution_update_timestamp",
        "late_probability_move_timestamp",
        "late_follow_up_source_timestamp",
        "late_resolution_update_timestamp",
    )
    assert len(timeline_report.report_digest) == 64
    assert timeline_report.report_digest == repeated_report.report_digest
    assert timeline_report.paper_only is True
    assert timeline_report.report_only is True
    assert timeline_report.readonly is True

    assert tuple(row.packet_ref for row in timeline_report.rows) == (
        "packet-missing",
        "packet-late",
        "packet-complete",
    )

    missing = timeline_report.rows[0]
    assert type(missing) is module.ResearchPacketEventTimelineCompletenessV2Row
    assert missing.row_status == "blocked"
    assert missing.present_step_count == d("3")
    assert missing.complete_step_count == d("2")
    assert missing.missing_step_count == d("2")
    assert missing.late_step_count == d("1")
    assert missing.completeness_ratio == d("0.400000")
    assert missing.missing_step_codes == (
        "missing_primary_source_timestamp",
        "missing_resolution_update_timestamp",
    )
    assert missing.late_step_codes == ("late_probability_move_timestamp",)
    assert missing.reason_codes == (
        "event_timeline_missing_steps",
        "event_timeline_late_steps",
        "missing_primary_source_timestamp",
        "missing_resolution_update_timestamp",
        "late_probability_move_timestamp",
    )
    assert len(missing.timeline_digest) == 64
    assert missing.timeline_digest == repeated_report.rows[0].timeline_digest

    late = timeline_report.rows[1]
    assert late.row_status == "watch"
    assert late.present_step_count == d("5")
    assert late.complete_step_count == d("3")
    assert late.missing_step_count == d("0")
    assert late.late_step_count == d("2")
    assert late.completeness_ratio == d("0.600000")
    assert late.late_step_codes == (
        "late_follow_up_source_timestamp",
        "late_resolution_update_timestamp",
    )
    assert late.reason_codes == (
        "event_timeline_late_steps",
        "late_follow_up_source_timestamp",
        "late_resolution_update_timestamp",
    )

    complete = timeline_report.rows[2]
    assert complete.row_status == "complete"
    assert complete.present_step_count == d("5")
    assert complete.complete_step_count == d("5")
    assert complete.completeness_ratio == d("1.000000")
    assert complete.reason_codes == ("event_timeline_completeness_complete",)


def test_empty_report_is_complete_with_decimal_zero_counts() -> None:
    timeline_report = report()

    assert timeline_report.report_status == "complete"
    assert timeline_report.source_packet_count == d("0")
    assert timeline_report.complete_packet_count == d("0")
    assert timeline_report.watch_packet_count == d("0")
    assert timeline_report.blocked_packet_count == d("0")
    assert timeline_report.required_step_count == d("0")
    assert timeline_report.complete_step_count == d("0")
    assert timeline_report.missing_step_count == d("0")
    assert timeline_report.late_step_count == d("0")
    assert timeline_report.completeness_ratio == d("1.000000")
    assert timeline_report.reason_codes == ("event_timeline_completeness_complete",)
    assert timeline_report.rows == ()
    assert len(timeline_report.report_digest) == 64


def test_inputs_validate_time_decimal_identity_flags_and_duplicates() -> None:
    module = api()

    with pytest.raises(ValueError, match="late_after_packet_grace_seconds must be a Decimal"):
        config(late_after_packet_grace_seconds=0)

    with pytest.raises(ValueError, match="packet_generated_at must be timezone-aware"):
        packet(
            "packet-naive",
            packet_generated_at=datetime(2026, 7, 2, 10, 0),
        )

    offset_report = report(
        packet(
            "packet-offset",
            packet_generated_at=datetime(
                2026,
                7,
                2,
                6,
                0,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
            initial_catalyst_at=datetime(
                2026,
                7,
                2,
                5,
                0,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
            primary_source_timestamp_at=datetime(
                2026,
                7,
                2,
                5,
                15,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
            probability_move_timestamp_at=datetime(
                2026,
                7,
                2,
                5,
                30,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
            follow_up_source_timestamp_at=datetime(
                2026,
                7,
                2,
                5,
                45,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
            resolution_update_timestamp_at=datetime(
                2026,
                7,
                2,
                5,
                55,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
        ),
    )
    assert offset_report.rows[0].packet_generated_at == GENERATED_AT - timedelta(hours=1)
    assert offset_report.rows[0].initial_catalyst_at == GENERATED_AT - timedelta(hours=2)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_event_timeline_completeness_v2_report(
            (packet("packet-generated"),),
            config=config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="probability_move_timestamp_at must not be after generated_at"):
        report(
            packet(
                "packet-future",
                probability_move_timestamp_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    with pytest.raises(ValueError, match="packet_ref values must be unique"):
        report(packet("packet-dup"), packet("packet-dup"))

    item = packet("packet-frozen")
    with pytest.raises(FrozenInstanceError):
        item.packet_ref = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        module.ResearchPacketEventTimelineCompletenessV2Config(report_only=False)


def test_payload_is_json_ready_without_float_values_or_external_action_surface() -> None:
    module = api()
    timeline_report = report(
        packet(
            "packet-json",
            packet_generated_at=GENERATED_AT - timedelta(hours=1),
            follow_up_source_timestamp_at=GENERATED_AT - timedelta(minutes=30),
        ),
    )

    payload = module.research_packet_event_timeline_completeness_v2_report_to_payload(
        timeline_report,
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["source_packet_count"] == "1"
    assert payload["completeness_ratio"] == "0.800000"
    assert payload["rows"][0]["late_step_count"] == "1"
    assert payload["rows"][0]["late_step_codes"] == ["late_follow_up_source_timestamp"]
    assert_no_float(payload)
    json.dumps(payload)

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
