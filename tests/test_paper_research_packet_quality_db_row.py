from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketConfig,
    PaperResearchPacketInputRow,
    build_paper_research_packet_report,
)
from polymarket_alpha_lab.paper_research_packet_quality import (
    PaperResearchPacketQualityCheckRow,
    PaperResearchPacketQualityConfig,
    PaperResearchPacketQualityReport,
    build_paper_research_packet_quality_report,
)


GENERATED_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 23, 11, 55, tzinfo=UTC)


class ResearchPacketQualityReportSubclass(PaperResearchPacketQualityReport):
    pass


class ResearchPacketQualityCheckRowSubclass(PaperResearchPacketQualityCheckRow):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_research_packet_quality_db_row

    return paper_research_packet_quality_db_row


def _d(value: str) -> Decimal:
    return Decimal(value)


def _input_row(
    market_slug: str,
    *,
    side: str = "yes",
    action: str = "recommend",
    queue_status: str = "ready",
    recommendation_score: Decimal = _d("0.800000"),
    net_edge: Decimal = _d("0.060000"),
    reason_codes: tuple[str, ...] = ("positive_edge",),
) -> PaperResearchPacketInputRow:
    return PaperResearchPacketInputRow(
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        side=side,
        action=action,
        queue_status=queue_status,
        recommendation_score=recommendation_score,
        net_edge=net_edge,
        allocated_notional=_d("5.000000") if side != "none" else None,
        requested_notional=_d("8.000000") if side != "none" else None,
        reason_codes=reason_codes,
    )


def _skip_row(market_slug: str) -> PaperResearchPacketInputRow:
    return _input_row(
        market_slug,
        side="none",
        action="reject",
        queue_status="blocked",
        recommendation_score=_d("0.000000"),
        net_edge=_d("0.000000"),
        reason_codes=("manual_reject",),
    )


def _packet_report(rows: tuple[PaperResearchPacketInputRow, ...]):
    return build_paper_research_packet_report(
        rows,
        config=PaperResearchPacketConfig(
            config_version="paper-research-packet-v0",
            max_packet_rows=10,
            min_score=_d("0.200000"),
        ),
        generated_at=SOURCE_AT,
    )


def _report() -> PaperResearchPacketQualityReport:
    packet_report = _packet_report(
        (
            _input_row("alpha", reason_codes=("shared_reason", "alpha_edge")),
            _input_row(
                "beta",
                recommendation_score=_d("0.700000"),
                net_edge=_d("0.030000"),
                reason_codes=("shared_reason", "beta_edge"),
            ),
            _skip_row("gamma"),
        ),
    )
    return build_paper_research_packet_quality_report(
        packet_report,
        config=PaperResearchPacketQualityConfig(),
        generated_at=GENERATED_AT,
    )


def _empty_report() -> PaperResearchPacketQualityReport:
    return build_paper_research_packet_quality_report(
        _packet_report(()),
        config=PaperResearchPacketQualityConfig(),
        generated_at=GENERATED_AT,
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_quality_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperResearchPacketQualityDbRow
    assert len(row.report_sha256) == 64
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-research-packet-quality-v0"
    assert row.source_generated_at == SOURCE_AT
    assert row.source_config_version == "paper-research-packet-v0"
    assert row.input_row_count == 3
    assert row.packet_row_count == 3
    assert row.included_count == 2
    assert row.skipped_count == 1
    assert row.high_priority_count == 1
    assert row.medium_priority_count == 1
    assert row.low_priority_count == 0
    assert row.source_age_seconds == 300
    assert row.included_share == _d("0.666667")
    assert row.skipped_share == _d("0.333333")
    assert row.check_count == 3
    assert row.pass_count == 3
    assert row.watch_count == 0
    assert row.blocked_count == 0
    assert row.quality_status == "pass"
    assert row.check_rows_json == [
        {
            "check_name": "source_freshness",
            "status": "pass",
            "observed_value": 300,
            "threshold": 21600,
            "reason_codes": ["source_freshness_passed"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "check_name": "packet_population",
            "status": "pass",
            "observed_value": 2,
            "threshold": 1,
            "reason_codes": ["packet_population_passed"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "check_name": "skip_pressure",
            "status": "pass",
            "observed_value": "0.333333",
            "threshold": "0.500000",
            "reason_codes": ["skip_pressure_passed"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.reason_code_counts_json[0] == {
        "reason_code": "shared_reason",
        "count": 2,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert row.reason_codes_json == [
        item["reason_code"] for item in row.reason_code_counts_json
    ]
    assert row.reason_code_count == len(row.reason_codes_json)
    assert row.payload_json["generated_at"] == "2026-06-23T12:00:00+00:00"
    assert row.payload_json["source_generated_at"] == "2026-06-23T11:55:00+00:00"
    assert row.payload_json["included_share"] == "0.666667"
    assert row.payload_json["skipped_share"] == "0.333333"
    assert row.payload_json["check_rows"] == row.check_rows_json
    assert row.payload_json["reason_code_counts"] == row.reason_code_counts_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.check_rows_json)
    _assert_no_floats(row.reason_code_counts_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.from_db_row(row) == report
    assert codec.paper_research_packet_quality_report_to_db_row(report) == row
    assert codec.paper_research_packet_quality_report_from_db_row(row) == report


def test_quality_db_row_handles_absent_ratio_values() -> None:
    codec = _codec_module()
    report = _empty_report()

    row = codec.to_db_row(report)

    assert row.packet_row_count == 0
    assert row.included_share is None
    assert row.skipped_share is None
    assert row.payload_json["included_share"] is None
    assert row.payload_json["skipped_share"] is None
    assert row.quality_status == "blocked"
    assert codec.from_db_row(row) == report


def test_quality_db_row_hash_is_deterministic() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperResearchPacketQualityReport(**report.__dict__)
    different_report = PaperResearchPacketQualityReport(
        **{**report.__dict__, "config_version": "paper-research-packet-quality-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_quality_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_quality_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperResearchPacketQualityReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperResearchPacketQualityReport"):
        codec.to_db_row(ResearchPacketQualityReportSubclass(**report.__dict__))


def test_quality_db_row_rejects_nested_check_row_subclasses() -> None:
    codec = _codec_module()
    report = _report()
    nested_row = ResearchPacketQualityCheckRowSubclass(**report.check_rows[0].__dict__)
    object.__setattr__(report, "check_rows", (nested_row, *report.check_rows[1:]))

    with pytest.raises(ValueError, match="PaperResearchPacketQualityCheckRow"):
        codec.to_db_row(report)


def test_quality_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class ResearchPacketQualityDbRowSubclass(codec.PaperResearchPacketQualityDbRow):
        pass

    with pytest.raises(ValueError, match="PaperResearchPacketQualityDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperResearchPacketQualityDbRow"):
        codec.from_db_row(ResearchPacketQualityDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_quality_db_row_rejects_false_report_flags_before_write(flag_name: str) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_quality_db_row_rejects_false_nested_report_flags_before_write() -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report.check_rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_quality_db_row_rejects_corrupted_nested_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperResearchPacketQualityDbRow(
        **{
            **_row_values(row),
            "payload_json": {
                **row.payload_json,
                "check_rows": [
                    {**row.payload_json["check_rows"][0], "readonly": False},
                    *row.payload_json["check_rows"][1:],
                ],
            },
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_quality_db_row_rejects_missing_selected_check_row_hard_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperResearchPacketQualityDbRow(
            **{
                **_row_values(row),
                "check_rows_json": [
                    {
                        key: value
                        for key, value in row.check_rows_json[0].items()
                        if key not in {"paper_only", "report_only", "readonly"}
                    },
                    *row.check_rows_json[1:],
                ],
            },
        )


def test_quality_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperResearchPacketQualityDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 23, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-research-packet-quality-v1"}, "config_version"),
        ({"source_generated_at": datetime(2026, 6, 23, 11, 54, tzinfo=UTC)}, "source_generated_at"),
        ({"source_config_version": "paper-research-packet-v1"}, "source_config_version"),
        ({"input_row_count": 4}, "input_row_count"),
        ({"packet_row_count": 2}, "packet_row_count"),
        ({"included_count": 1}, "included_count"),
        ({"skipped_count": 2}, "skipped_count"),
        ({"high_priority_count": 0}, "high_priority_count"),
        ({"medium_priority_count": 0}, "medium_priority_count"),
        ({"source_age_seconds": 301}, "source_age_seconds"),
        ({"included_share": _d("0.333333")}, "included_share"),
        ({"skipped_share": _d("0.666667")}, "skipped_share"),
        ({"quality_status": "watch"}, "quality_status"),
        ({"pass_count": 2}, "pass_count"),
        ({"check_rows_json": []}, "check_rows_json"),
        ({"reason_code_counts_json": []}, "reason_code_counts_json"),
        ({"reason_codes_json": ["source_freshness_passed"]}, "reason_codes"),
        ({"reason_code_count": 1}, "reason_code_count"),
    ),
)
def test_quality_db_row_rejects_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperResearchPacketQualityDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"quality_status": "stable"}, "quality_status"),
        ({"input_row_count": True}, "input_row_count"),
        ({"included_share": _d("1.000001")}, "included_share"),
        ({"skipped_share": 0.1}, "skipped_share"),
        ({"check_rows_json": "source_freshness"}, "check_rows_json"),
        ({"check_rows_json": [{"check_name": "source_freshness"}]}, "check_rows_json"),
        ({"reason_code_counts_json": "source_freshness_passed"}, "reason_code_counts_json"),
        ({"reason_code_counts_json": [{"reason_code": "x", "count": 0}]}, "reason_code_counts_json"),
        ({"reason_codes_json": "source_freshness_passed"}, "reason_codes_json"),
        ({"reason_code_count": -1}, "reason_code_count"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_quality_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperResearchPacketQualityDbRow(
            **{**_row_values(row), **overrides},
        )


def test_quality_db_row_module_is_pure_paper_only_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_research_packet_quality_db_row.py",
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
