import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.rejections import RejectedCandidateLog, RejectedCandidateRecord
from polymarket_alpha_lab.research import build_research_packet
from polymarket_alpha_lab.risk import RiskGateConfig, evaluate_research_packet_risk


def complete_packet(**overrides):
    values = {
        "candidate": ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        "created_at": datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        "market_url": "https://polymarket.com/event/example-market",
        "outcome_name": "Yes",
        "strategy_type": "market_quality",
        "model_probability": Decimal("0.56"),
        "bid": Decimal("0.50"),
        "ask": Decimal("0.52"),
        "midpoint": Decimal("0.51"),
        "expected_entry_price": Decimal("0.514"),
        "fair_value_estimate": Decimal("0.56"),
        "theoretical_edge": Decimal("0.046"),
        "spread": Decimal("0.02"),
        "slippage_estimate": Decimal("0.004"),
        "cost_adjusted_edge": Decimal("-0.010"),
        "confidence": Decimal("0.40"),
        "max_executable_size": Decimal("100"),
        "risk_tags": ("liquidity",),
        "thesis": "Tight spread and clear rules.",
        "invalidating_conditions": "Spread widens.",
        "rule_text": "Example rule.",
        "resolution_source": "Example source",
    }
    values.update(overrides)
    return build_research_packet(**values)


def rejected_decision(packet=None):
    return evaluate_research_packet_risk(
        packet or complete_packet(),
        RiskGateConfig(
            config_version="v1",
            min_confidence=Decimal("0.55"),
            min_cost_adjusted_edge=Decimal("0.00"),
        ),
    )


def test_rejected_candidate_log_appends_jsonl_record(tmp_path):
    packet = complete_packet()
    decision = rejected_decision(packet)
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=decision,
        rejected_at=datetime(2026, 6, 13, 12, 31),
        evidence_summary="Cost-adjusted edge and confidence failed.",
    )
    log = RejectedCandidateLog(path=tmp_path / "rejected-candidates.jsonl")

    log.append(record)

    lines = log.path.read_text().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"condition_id"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["rejected_at"] == "2026-06-13T12:31:00+00:00"
    assert stored["packet_id"] == packet.packet_id
    assert stored["condition_id"] == "0xabc"
    assert stored["token_id"] == "111"
    assert stored["market_slug"] == "example-market"
    assert stored["market_url"] == "https://polymarket.com/event/example-market"
    assert stored["strategy_type"] == "market_quality"
    assert stored["market_raw_archive_path"] == "data/raw/gamma/markets.json"
    assert stored["rule_text_hash"] == packet.rule_text_hash
    assert stored["risk_tags"] == ["liquidity"]
    assert stored["gate_config_version"] == "v1"
    assert [reason["code"] for reason in stored["reasons"]] == [
        "low_confidence",
        "low_cost_adjusted_edge",
    ]
    assert stored["reasons"][0]["observed_value"] == "0.40"
    assert stored["evidence_summary"] == "Cost-adjusted edge and confidence failed."


def test_rejected_candidate_log_appends_without_overwriting(tmp_path):
    packet = complete_packet()
    decision = rejected_decision(packet)
    log = RejectedCandidateLog(path=str(tmp_path / "nested" / "rejected.jsonl"))
    first = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=decision,
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="First rejection.",
    )
    second = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=decision,
        rejected_at=datetime(2026, 6, 13, 12, 32, tzinfo=UTC),
        evidence_summary="Second rejection.",
    )

    log.append(first)
    log.append(second)

    lines = log.path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["evidence_summary"] == "First rejection."
    assert json.loads(lines[1])["evidence_summary"] == "Second rejection."


def test_rejected_candidate_log_rejects_invalid_paths(tmp_path):
    with pytest.raises(ValueError, match="path"):
        RejectedCandidateLog(path=object())
    with pytest.raises(ValueError, match="path"):
        RejectedCandidateLog(path="")
    with pytest.raises(ValueError, match="path"):
        RejectedCandidateLog(path=tmp_path)
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="path"):
        RejectedCandidateLog(path=parent_file / "rejected.jsonl")
    with pytest.raises(ValueError, match="path"):
        RejectedCandidateLog(path=parent_file / "nested" / "rejected.jsonl")


def test_rejected_candidate_log_supports_incomplete_packet_rejections(tmp_path):
    packet = complete_packet(
        market_url="",
        outcome_name="",
        strategy_type="",
        confidence=None,
        risk_tags=(),
    )
    decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=decision,
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Packet was missing fields required for review.",
    )
    log = RejectedCandidateLog(path=tmp_path / "rejected.jsonl")

    log.append(record)

    stored = json.loads(log.path.read_text())
    assert stored["market_url"] == ""
    assert stored["outcome_name"] == ""
    assert stored["strategy_type"] == ""
    assert stored["risk_tags"] == []
    assert stored["reasons"][0]["code"] == "incomplete_packet"
    assert "confidence" in stored["reasons"][0]["observed_value"]


def test_rejected_candidate_record_normalizes_rejected_at_to_utc():
    eastern = timezone(timedelta(hours=-4))
    packet = complete_packet()
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=rejected_decision(packet),
        rejected_at=datetime(2026, 6, 13, 8, 31, tzinfo=eastern),
        evidence_summary="Rejected.",
    )

    assert record.rejected_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)


def test_rejected_candidate_record_rejects_accepted_decision():
    packet = complete_packet(cost_adjusted_edge=Decimal("0.020"), confidence=Decimal("0.80"))
    accepted_decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )

    with pytest.raises(ValueError, match="accepted"):
        RejectedCandidateRecord.from_packet_and_decision(
            packet=packet,
            decision=accepted_decision,
            rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            evidence_summary="Should not reject.",
        )


def test_rejected_candidate_record_rejects_invalid_public_inputs():
    packet = complete_packet()
    decision = rejected_decision(packet)

    with pytest.raises(ValueError, match="packet"):
        RejectedCandidateRecord.from_packet_and_decision(
            packet=object(),
            decision=decision,
            rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            evidence_summary="Rejected.",
        )
    with pytest.raises(ValueError, match="decision"):
        RejectedCandidateRecord.from_packet_and_decision(
            packet=packet,
            decision=object(),
            rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            evidence_summary="Rejected.",
        )


def test_rejected_candidate_record_rejects_packet_with_invalid_risk_tags():
    packet = replace(complete_packet(), risk_tags=None)
    decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )

    with pytest.raises(ValueError, match="risk_tags"):
        RejectedCandidateRecord.from_packet_and_decision(
            packet=packet,
            decision=decision,
            rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            evidence_summary="Rejected.",
        )


@pytest.mark.parametrize("evidence_summary", ["", "   ", None, 123])
def test_rejected_candidate_record_rejects_blank_evidence_summary(evidence_summary):
    packet = complete_packet()

    with pytest.raises(ValueError, match="evidence_summary"):
        RejectedCandidateRecord.from_packet_and_decision(
            packet=packet,
            decision=rejected_decision(packet),
            rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            evidence_summary=evidence_summary,
        )


def test_rejected_candidate_record_rejects_invalid_direct_record_state():
    packet = complete_packet()
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=rejected_decision(packet),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Rejected.",
    )

    with pytest.raises(ValueError, match="paper_only"):
        replace(record, paper_only=False)
    with pytest.raises(ValueError, match="risk_tags"):
        replace(record, risk_tags=(123,))
    with pytest.raises(ValueError, match="reasons"):
        replace(record, reasons=("bad",))
    with pytest.raises(ValueError, match="reasons"):
        replace(record, reasons=None)
    with pytest.raises(ValueError, match="evidence_summary"):
        replace(record, evidence_summary=123)


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("packet_id", 123),
        ("packet_id", ""),
        ("condition_id", ""),
        ("token_id", ""),
        ("market_slug", ""),
        ("question", ""),
        ("source_score", ""),
        ("market_raw_archive_path", ""),
        ("rule_text_hash", ""),
        ("resolution_source", ""),
        ("gate_config_version", None),
        ("market_url", object()),
        ("outcome_name", object()),
        ("strategy_type", object()),
    ],
)
def test_rejected_candidate_record_rejects_invalid_direct_scalar_fields(
    field_name,
    bad_value,
):
    packet = complete_packet()
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=rejected_decision(packet),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Rejected.",
    )

    with pytest.raises(ValueError, match=field_name):
        replace(record, **{field_name: bad_value})


def test_rejected_candidate_record_direct_construction_normalizes_timestamps():
    packet = complete_packet()
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=rejected_decision(packet),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Rejected.",
    )
    eastern = timezone(timedelta(hours=-4))

    normalized = replace(
        record,
        rejected_at=datetime(2026, 6, 13, 8, 31, tzinfo=eastern),
        packet_created_at=datetime(2026, 6, 13, 8, 30, tzinfo=eastern),
    )

    assert normalized.rejected_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert normalized.packet_created_at == datetime(2026, 6, 13, 12, 30, tzinfo=UTC)


def test_rejected_candidate_log_rejects_non_finite_reason_decimal(tmp_path):
    packet = complete_packet()
    decision = rejected_decision(packet)
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=replace(
            decision,
            reasons=(
                replace(decision.reasons[0], observed_value=Decimal("NaN")),
            ),
        ),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Bad decimal.",
    )
    log = RejectedCandidateLog(path=tmp_path / "rejected.jsonl")

    with pytest.raises(ValueError, match="finite"):
        log.append(record)

    assert not log.path.exists()


def test_rejected_candidate_log_rejects_non_finite_reason_threshold(tmp_path):
    packet = complete_packet()
    decision = rejected_decision(packet)
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=replace(
            decision,
            reasons=(
                replace(decision.reasons[0], threshold=Decimal("Infinity")),
            ),
        ),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Bad threshold.",
    )
    log = RejectedCandidateLog(path=tmp_path / "rejected.jsonl")

    with pytest.raises(ValueError, match="finite"):
        log.append(record)

    assert not log.path.exists()


def test_rejected_candidate_log_rejects_non_finite_float_before_open(tmp_path):
    packet = complete_packet()
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=rejected_decision(packet),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Bad float.",
    )
    object.__setattr__(record, "source_score", float("nan"))
    log = RejectedCandidateLog(path=tmp_path / "rejected.jsonl")

    with pytest.raises(ValueError, match="finite"):
        log.append(record)

    assert not log.path.exists()


def test_rejected_candidate_log_rejects_invalid_public_input(tmp_path):
    log = RejectedCandidateLog(path=tmp_path / "rejected.jsonl")

    with pytest.raises(ValueError, match="record"):
        log.append(object())

    assert not log.path.exists()
