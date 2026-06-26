from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketReport,
    PaperResearchPacketRow,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow import (
    PaperResearchPacketOperatorFlowConfig,
    PaperResearchPacketOperatorFlowReport,
    build_paper_research_packet_operator_flow_report,
)
from polymarket_alpha_lab.paper_research_packet_quality import (
    PaperResearchPacketQualityCheckRow,
    PaperResearchPacketQualityReasonCodeCount,
    PaperResearchPacketQualityReport,
)
from polymarket_alpha_lab.paper_research_packet_quality_history import (
    PaperResearchPacketQualityHistoryCheckSummaryRow,
    PaperResearchPacketQualityHistoryRecurringReasonCodeRow,
    PaperResearchPacketQualityHistoryReport,
    PaperResearchPacketQualityHistoryStatusRow,
)


PACKET_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
QUALITY_AT = datetime(2026, 6, 23, 12, 30, tzinfo=UTC)
HISTORY_AT = datetime(2026, 6, 23, 13, 0, tzinfo=UTC)
GENERATED_AT = datetime(2026, 6, 23, 13, 5, tzinfo=UTC)


class OperatorFlowReportSubclass(PaperResearchPacketOperatorFlowReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_research_packet_operator_flow_db_row

    return paper_research_packet_operator_flow_db_row


def _packet_report() -> PaperResearchPacketReport:
    return PaperResearchPacketReport(
        generated_at=PACKET_AT,
        config_version="paper-research-packet-v1",
        input_row_count=2,
        packet_row_count=1,
        included_count=1,
        skipped_count=0,
        high_priority_count=1,
        medium_priority_count=0,
        low_priority_count=0,
        packet_rows=(
            PaperResearchPacketRow(
                packet_rank=1,
                market_slug="election-alpha",
                question="Will election alpha resolve yes?",
                side="yes",
                research_priority="high",
                required_checks=(
                    "outcome_definition",
                    "liquidity_depth",
                    "cost_sensitivity",
                    "settlement_timing",
                ),
                reason_codes=("positive_edge",),
                recommendation_score=Decimal("0.910000"),
                net_edge=Decimal("0.080000"),
                allocated_notional=Decimal("12.500000"),
                requested_notional=Decimal("15.000000"),
            ),
        ),
    )


def _quality_report() -> PaperResearchPacketQualityReport:
    check_rows = (
        PaperResearchPacketQualityCheckRow(
            check_name="source_freshness",
            status="pass",
            observed_value=1_800,
            threshold=21_600,
            reason_codes=("source_freshness_passed",),
        ),
        PaperResearchPacketQualityCheckRow(
            check_name="packet_population",
            status="pass",
            observed_value=1,
            threshold=1,
            reason_codes=("packet_population_passed",),
        ),
        PaperResearchPacketQualityCheckRow(
            check_name="skip_pressure",
            status="pass",
            observed_value=Decimal("0.000000"),
            threshold=Decimal("0.500000"),
            reason_codes=("skip_pressure_passed",),
        ),
    )
    return PaperResearchPacketQualityReport(
        generated_at=QUALITY_AT,
        config_version="paper-research-packet-quality-v1",
        source_generated_at=PACKET_AT,
        source_config_version="paper-research-packet-v1",
        input_row_count=2,
        packet_row_count=1,
        included_count=1,
        skipped_count=0,
        high_priority_count=1,
        medium_priority_count=0,
        low_priority_count=0,
        source_age_seconds=1_800,
        included_share=Decimal("1.000000"),
        skipped_share=Decimal("0.000000"),
        check_count=3,
        pass_count=3,
        watch_count=0,
        blocked_count=0,
        quality_status="pass",
        check_rows=check_rows,
        reason_code_counts=(
            PaperResearchPacketQualityReasonCodeCount(
                reason_code="packet_population_passed",
                count=1,
            ),
            PaperResearchPacketQualityReasonCodeCount(
                reason_code="positive_edge",
                count=1,
            ),
            PaperResearchPacketQualityReasonCodeCount(
                reason_code="skip_pressure_passed",
                count=1,
            ),
            PaperResearchPacketQualityReasonCodeCount(
                reason_code="source_freshness_passed",
                count=1,
            ),
        ),
    )


def _history_report(
    quality_report: PaperResearchPacketQualityReport,
) -> PaperResearchPacketQualityHistoryReport:
    latest_check_rows = (
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            check_name="source_freshness",
            status="pass",
            reason_codes=("source_freshness_passed",),
        ),
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            check_name="packet_population",
            status="pass",
            reason_codes=("packet_population_passed",),
        ),
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            check_name="skip_pressure",
            status="pass",
            reason_codes=("skip_pressure_passed",),
        ),
    )
    return PaperResearchPacketQualityHistoryReport(
        generated_at=HISTORY_AT,
        config_version="paper-research-packet-quality-history-v1",
        history_status="pass",
        source_report_count=3,
        first_source_generated_at=quality_report.generated_at - timedelta(hours=2),
        latest_source_generated_at=quality_report.generated_at,
        latest_quality_status=quality_report.quality_status,
        latest_source_age_seconds=quality_report.source_age_seconds,
        latest_included_share=quality_report.included_share,
        latest_skipped_share=quality_report.skipped_share,
        latest_check_rows=latest_check_rows,
        quality_status_rows=(
            PaperResearchPacketQualityHistoryStatusRow(
                quality_status="pass",
                status_count=3,
            ),
            PaperResearchPacketQualityHistoryStatusRow(
                quality_status="watch",
                status_count=0,
            ),
            PaperResearchPacketQualityHistoryStatusRow(
                quality_status="blocked",
                status_count=0,
            ),
        ),
        duplicate_generated_at_count=0,
        recurring_reason_code_rows=(
            PaperResearchPacketQualityHistoryRecurringReasonCodeRow(
                check_status="watch",
                reason_code="watch_reason_not_present",
                report_count=2,
            ),
        ),
        reason_codes=("paper_research_packet_quality_history_passed",),
    )


def _report() -> PaperResearchPacketOperatorFlowReport:
    quality_report = _quality_report()
    return build_paper_research_packet_operator_flow_report(
        packet_report=_packet_report(),
        packet_persisted=True,
        quality_report=quality_report,
        quality_persisted=True,
        quality_history_report=_history_report(quality_report),
        config=PaperResearchPacketOperatorFlowConfig(),
        generated_at=GENERATED_AT,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _bypassed_row(row: object, **overrides: object) -> object:
    malformed = object.__new__(type(row))
    for field_name, value in {**_row_values(row), **overrides}.items():
        object.__setattr__(malformed, field_name, value)
    return malformed


def test_operator_flow_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperResearchPacketOperatorFlowDbRow
    assert len(row.report_sha256) == 64
    assert row.generated_at == report.generated_at
    assert row.config_version == report.config_version
    assert row.flow_status == report.flow_status
    assert row.packet_generated_at == report.packet_generated_at
    assert row.packet_config_version == report.packet_config_version
    assert row.packet_persisted == report.packet_persisted
    assert row.packet_row_count == report.packet_row_count
    assert row.included_count == report.included_count
    assert row.skipped_count == report.skipped_count
    assert row.quality_generated_at == report.quality_generated_at
    assert row.quality_config_version == report.quality_config_version
    assert row.quality_status == report.quality_status
    assert row.quality_persisted == report.quality_persisted
    assert row.quality_check_count == report.quality_check_count
    assert row.quality_pass_count == report.quality_pass_count
    assert row.quality_watch_count == report.quality_watch_count
    assert row.quality_blocked_count == report.quality_blocked_count
    assert row.history_generated_at == report.history_generated_at
    assert row.history_config_version == report.history_config_version
    assert row.history_status == report.history_status
    assert row.history_source_report_count == report.history_source_report_count
    assert row.history_latest_quality_status == report.history_latest_quality_status
    assert row.reason_codes_json == list(report.reason_codes)
    assert row.reason_code_count == len(report.reason_codes)
    assert row.payload_json["generated_at"] == report.generated_at.isoformat()
    assert row.payload_json["packet_generated_at"] == report.packet_generated_at.isoformat()
    assert row.payload_json["quality_generated_at"] == report.quality_generated_at.isoformat()
    assert row.payload_json["history_generated_at"] == report.history_generated_at.isoformat()
    assert row.payload_json["quality_included_share"] == "1.000000"
    assert row.payload_json["quality_skipped_share"] == "0.000000"
    assert row.payload_json["history_latest_included_share"] == "1.000000"
    assert row.payload_json["history_latest_skipped_share"] == "0.000000"
    assert row.payload_json["reason_codes"] == list(report.reason_codes)
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.reason_codes_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.from_db_row(row) == report
    assert codec.paper_research_packet_operator_flow_report_to_db_row(report) == row
    assert codec.paper_research_packet_operator_flow_report_from_db_row(row) == report


def test_operator_flow_db_row_hash_is_deterministic() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperResearchPacketOperatorFlowReport(**report.__dict__)
    different_report = PaperResearchPacketOperatorFlowReport(
        **{
            **report.__dict__,
            "config_version": "paper-research-packet-operator-flow-v1",
        },
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_operator_flow_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_operator_flow_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperResearchPacketOperatorFlowReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperResearchPacketOperatorFlowReport"):
        codec.to_db_row(OperatorFlowReportSubclass(**report.__dict__))


def test_operator_flow_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class OperatorFlowDbRowSubclass(codec.PaperResearchPacketOperatorFlowDbRow):
        pass

    with pytest.raises(ValueError, match="PaperResearchPacketOperatorFlowDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperResearchPacketOperatorFlowDbRow"):
        codec.from_db_row(OperatorFlowDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_operator_flow_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_operator_flow_db_row_rejects_corrupted_payload_hard_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperResearchPacketOperatorFlowDbRow(
            **{
                **_row_values(row),
                "payload_json": {**row.payload_json, "readonly": False},
            },
        )


def test_operator_flow_db_row_rejects_missing_payload_hard_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperResearchPacketOperatorFlowDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    key: value
                    for key, value in row.payload_json.items()
                    if key not in {"paper_only", "report_only", "readonly"}
                },
            },
        )


def test_operator_flow_db_row_rejects_nested_payload_hard_flag_corruption() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperResearchPacketOperatorFlowDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    **row.payload_json,
                    "nested_probe": {"paper_only": True, "report_only": True, "readonly": False},
                },
            },
        )


def test_operator_flow_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperResearchPacketOperatorFlowDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": GENERATED_AT + timedelta(minutes=1)}, "generated_at"),
        ({"config_version": "paper-research-packet-operator-flow-v1"}, "config_version"),
        ({"flow_status": "watch"}, "flow_status"),
        ({"packet_generated_at": PACKET_AT - timedelta(minutes=1)}, "packet_generated_at"),
        ({"packet_config_version": "paper-research-packet-v2"}, "packet_config_version"),
        ({"packet_persisted": False}, "packet_persisted"),
        ({"packet_row_count": 2}, "packet_row_count"),
        ({"included_count": 0}, "included_count"),
        ({"skipped_count": 1}, "skipped_count"),
        ({"quality_generated_at": QUALITY_AT + timedelta(minutes=1)}, "quality_generated_at"),
        ({"quality_config_version": "paper-research-packet-quality-v2"}, "quality_config_version"),
        ({"quality_status": "watch"}, "quality_status"),
        ({"quality_persisted": False}, "quality_persisted"),
        ({"quality_check_count": 4}, "quality_check_count"),
        ({"quality_pass_count": 2}, "quality_pass_count"),
        ({"quality_watch_count": 1}, "quality_watch_count"),
        ({"quality_blocked_count": 1}, "quality_blocked_count"),
        ({"history_generated_at": HISTORY_AT + timedelta(minutes=1)}, "history_generated_at"),
        ({"history_config_version": "paper-research-packet-quality-history-v2"}, "history_config_version"),
        ({"history_status": "watch"}, "history_status"),
        ({"history_source_report_count": 4}, "history_source_report_count"),
        ({"history_latest_quality_status": "watch"}, "history_latest_quality_status"),
        ({"reason_codes_json": ["other_operator_flow_reason"]}, "reason_codes_json"),
        ({"reason_code_count": 2}, "reason_code_count"),
        (
            {"payload_json": {**_report().__dict__, "generated_at": "2026-06-23T13:05:00Z"}},
            "payload_json",
        ),
    ),
)
def test_operator_flow_db_row_rejects_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    if "payload_json" in overrides:
        overrides = {
            **overrides,
            "payload_json": {**row.payload_json, **overrides["payload_json"]},  # type: ignore[arg-type]
        }
    with pytest.raises(ValueError, match=message):
        codec.PaperResearchPacketOperatorFlowDbRow(
            **{**_row_values(row), **overrides},
        )


def test_operator_flow_db_row_rejects_replacement_payload_mismatches() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="flow_status"):
        replace(row, flow_status="watch")


def test_operator_flow_from_db_row_rejects_object_new_bypassed_mismatches() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(row, report_sha256="b" * 64)

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


def test_operator_flow_from_db_row_rejects_object_new_bypassed_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(row, payload_json={**row.payload_json, "readonly": False})

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"flow_status": "stable"}, "flow_status"),
        ({"quality_status": "stable"}, "quality_status"),
        ({"history_status": "stable"}, "history_status"),
        ({"history_latest_quality_status": "stable"}, "history_latest_quality_status"),
        ({"packet_persisted": 1}, "packet_persisted"),
        ({"quality_persisted": 1}, "quality_persisted"),
        ({"packet_row_count": -1}, "packet_row_count"),
        ({"included_count": True}, "included_count"),
        ({"reason_codes_json": "operator_flow_passed"}, "reason_codes_json"),
        (
            {"reason_codes_json": ["operator_flow_passed", "operator_flow_passed"]},
            "reason_codes_json",
        ),
        ({"reason_codes_json": []}, "reason_codes_json"),
        ({"reason_code_count": True}, "reason_code_count"),
        ({"payload_json": []}, "payload_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_operator_flow_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperResearchPacketOperatorFlowDbRow(
            **{**_row_values(row), **overrides},
        )


def test_operator_flow_db_row_module_is_pure_paper_only_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "sql",
        "network",
        "client",
        "auth",
        "wallet",
        "account",
        "signing",
        "submission",
        "cancellation",
        "replacement",
        "exchange",
        "live_trading",
    ):
        assert banned not in source.lower()
