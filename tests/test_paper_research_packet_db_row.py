from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketReport,
    PaperResearchPacketRow,
)


GENERATED_AT = datetime(2026, 6, 22, 21, 0, tzinfo=UTC)


class ResearchPacketReportSubclass(PaperResearchPacketReport):
    pass


class ResearchPacketRowSubclass(PaperResearchPacketRow):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_research_packet_db_row

    return paper_research_packet_db_row


def _row(
    market_slug: str,
    *,
    question: str | None = None,
    side: str = "yes",
    research_priority: str = "high",
    required_checks: tuple[str, ...] = (
        "outcome_definition",
        "liquidity_depth",
        "cost_sensitivity",
        "settlement_timing",
    ),
    reason_codes: tuple[str, ...] = ("positive_edge", "settlement_review"),
    recommendation_score: Decimal = Decimal("0.910000"),
    net_edge: Decimal = Decimal("0.080000"),
    allocated_notional: Decimal | None = Decimal("12.500000"),
    requested_notional: Decimal | None = Decimal("15.000000"),
    packet_rank: int = 1,
) -> PaperResearchPacketRow:
    return PaperResearchPacketRow(
        packet_rank=packet_rank,
        market_slug=market_slug,
        question=question or f"Will {market_slug} resolve yes?",
        side=side,
        research_priority=research_priority,
        required_checks=required_checks,
        reason_codes=reason_codes,
        recommendation_score=recommendation_score,
        net_edge=net_edge,
        allocated_notional=allocated_notional,
        requested_notional=requested_notional,
    )


def _report() -> PaperResearchPacketReport:
    packet_rows = (
        _row("high-ready"),
        _row(
            "skip-blocked",
            question="Will skip-blocked resolve?",
            side="none",
            research_priority="skip",
            required_checks=("outcome_definition",),
            reason_codes=("blocked_source",),
            recommendation_score=Decimal("0.050000"),
            net_edge=Decimal("0.000000"),
            allocated_notional=None,
            requested_notional=None,
            packet_rank=2,
        ),
    )
    return PaperResearchPacketReport(
        generated_at=GENERATED_AT,
        config_version="paper-research-packet-v0",
        input_row_count=3,
        packet_row_count=2,
        included_count=1,
        skipped_count=1,
        high_priority_count=1,
        medium_priority_count=0,
        low_priority_count=0,
        packet_rows=packet_rows,
    )


def _empty_report() -> PaperResearchPacketReport:
    return PaperResearchPacketReport(
        generated_at=GENERATED_AT,
        config_version="paper-research-packet-v0",
        input_row_count=0,
        packet_row_count=0,
        included_count=0,
        skipped_count=0,
        high_priority_count=0,
        medium_priority_count=0,
        low_priority_count=0,
        packet_rows=(),
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _bypassed_row(row: object, **overrides: object) -> object:
    malformed = object.__new__(type(row))
    for field_name, value in {**_row_values(row), **overrides}.items():
        object.__setattr__(malformed, field_name, value)
    return malformed


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_research_packet_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperResearchPacketDbRow
    assert len(row.report_sha256) == 64
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-research-packet-v0"
    assert row.input_row_count == 3
    assert row.packet_row_count == 2
    assert row.included_count == 1
    assert row.skipped_count == 1
    assert row.high_priority_count == 1
    assert row.medium_priority_count == 0
    assert row.low_priority_count == 0
    assert row.packet_rows_json[0] == {
        "packet_rank": 1,
        "market_slug": "high-ready",
        "question": "Will high-ready resolve yes?",
        "side": "yes",
        "research_priority": "high",
        "required_checks": [
            "outcome_definition",
            "liquidity_depth",
            "cost_sensitivity",
            "settlement_timing",
        ],
        "reason_codes": ["positive_edge", "settlement_review"],
        "recommendation_score": "0.910000",
        "net_edge": "0.080000",
        "allocated_notional": "12.500000",
        "requested_notional": "15.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert row.packet_rows_json[1]["research_priority"] == "skip"
    assert row.packet_rows_json[1]["required_checks"] == ["outcome_definition"]
    assert row.payload_json["generated_at"] == "2026-06-22T21:00:00+00:00"
    assert row.payload_json["packet_rows"] == row.packet_rows_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.packet_rows_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.from_db_row(row) == report
    assert codec.paper_research_packet_report_to_db_row(report) == row
    assert codec.paper_research_packet_report_from_db_row(row) == report


def test_research_packet_db_row_handles_empty_reports() -> None:
    codec = _codec_module()
    report = _empty_report()

    row = codec.to_db_row(report)

    assert row.input_row_count == 0
    assert row.packet_row_count == 0
    assert row.included_count == 0
    assert row.skipped_count == 0
    assert row.packet_rows_json == []
    assert row.payload_json["packet_rows"] == []
    assert codec.from_db_row(row) == report


def test_research_packet_db_row_hash_is_deterministic() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperResearchPacketReport(**report.__dict__)
    different_report = PaperResearchPacketReport(
        **{
            **report.__dict__,
            "config_version": "paper-research-packet-v1",
        },
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_research_packet_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_research_packet_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperResearchPacketReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperResearchPacketReport"):
        codec.to_db_row(ResearchPacketReportSubclass(**report.__dict__))


def test_research_packet_db_row_rejects_nested_packet_row_subclasses() -> None:
    codec = _codec_module()
    report = _report()
    nested_row = ResearchPacketRowSubclass(**report.packet_rows[0].__dict__)
    object.__setattr__(
        report,
        "packet_rows",
        (nested_row, report.packet_rows[1]),
    )

    with pytest.raises(ValueError, match="PaperResearchPacketRow"):
        codec.to_db_row(report)


def test_research_packet_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class ResearchPacketDbRowSubclass(codec.PaperResearchPacketDbRow):
        pass

    with pytest.raises(ValueError, match="PaperResearchPacketDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperResearchPacketDbRow"):
        codec.from_db_row(ResearchPacketDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_research_packet_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_research_packet_db_row_rejects_corrupted_nested_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperResearchPacketDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    **row.payload_json,
                    "packet_rows": [
                        {
                            **row.payload_json["packet_rows"][0],
                            "readonly": False,
                        },
                        *row.payload_json["packet_rows"][1:],
                    ],
                },
            },
        )


def test_research_packet_db_row_rejects_missing_payload_hard_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperResearchPacketDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    key: value
                    for key, value in row.payload_json.items()
                    if key not in {"paper_only", "report_only", "readonly"}
                },
            },
        )


def test_research_packet_db_row_rejects_missing_payload_packet_row_hard_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperResearchPacketDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    **row.payload_json,
                    "packet_rows": [
                        {
                            key: value
                            for key, value in row.payload_json["packet_rows"][0].items()
                            if key not in {"paper_only", "report_only", "readonly"}
                        },
                        *row.payload_json["packet_rows"][1:],
                    ],
                },
            },
        )


def test_research_packet_db_row_rejects_missing_packet_rows_json_hard_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperResearchPacketDbRow(
            **{
                **_row_values(row),
                "packet_rows_json": [
                    {
                        key: value
                        for key, value in row.packet_rows_json[0].items()
                        if key not in {"paper_only", "report_only", "readonly"}
                    },
                    *row.packet_rows_json[1:],
                ],
            },
        )


def test_research_packet_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperResearchPacketDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 22, 21, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-research-packet-v1"}, "config_version"),
        ({"input_row_count": 4}, "input_row_count"),
        ({"packet_row_count": 3}, "packet_row_count"),
        ({"included_count": 2}, "included_count"),
        ({"skipped_count": 0}, "skipped_count"),
        ({"high_priority_count": 0}, "high_priority_count"),
        ({"medium_priority_count": 1}, "medium_priority_count"),
        ({"low_priority_count": 1}, "low_priority_count"),
        (
            {
                "packet_rows_json": [
                    {
                        **_report().packet_rows[0].__dict__,
                        "recommendation_score": "0.810000",
                        "required_checks": [
                            "outcome_definition",
                            "liquidity_depth",
                            "cost_sensitivity",
                            "settlement_timing",
                        ],
                        "reason_codes": ["positive_edge", "settlement_review"],
                        "net_edge": "0.080000",
                        "allocated_notional": "12.500000",
                        "requested_notional": "15.000000",
                    },
                    _codec_module().to_db_row(_report()).packet_rows_json[1],
                ],
            },
            "packet_rows_json",
        ),
    ),
)
def test_research_packet_db_row_rejects_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperResearchPacketDbRow(
            **{**_row_values(row), **overrides},
        )


def test_research_packet_db_row_rejects_replacement_payload_mismatches() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="included_count"):
        replace(row, included_count=row.included_count + 1)


def test_research_packet_from_db_row_rejects_object_new_bypassed_mismatches() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(row, report_sha256="b" * 64)

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


def test_research_packet_from_db_row_rejects_object_new_bypassed_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(
        row,
        payload_json={
            **row.payload_json,
            "packet_rows": [
                {**row.payload_json["packet_rows"][0], "readonly": False},
                *row.payload_json["packet_rows"][1:],
            ],
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"input_row_count": True}, "input_row_count"),
        ({"packet_rows_json": "high-ready"}, "packet_rows_json"),
        ({"packet_rows_json": [{"packet_rank": 1}]}, "packet_rows_json"),
        ({"payload_json": []}, "payload_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_research_packet_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperResearchPacketDbRow(
            **{**_row_values(row), **overrides},
        )


def test_research_packet_db_row_module_is_pure_paper_only_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_research_packet_db_row.py",
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
