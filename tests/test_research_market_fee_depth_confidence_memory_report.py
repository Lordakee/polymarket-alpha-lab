from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_fee_depth_confidence_memory_report import (
    ResearchMarketFeeDepthConfidenceMemoryConfig,
    ResearchMarketFeeDepthConfidenceMemoryObservation,
    ResearchMarketFeeDepthConfidenceMemoryReport,
    ResearchMarketFeeDepthConfidenceMemorySegment,
    build_research_market_fee_depth_confidence_memory_report,
    research_market_fee_depth_confidence_memory_public_payload,
    validate_research_market_fee_depth_confidence_memory_public_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketFeeDepthConfidenceMemoryConfig:
    values = {
        "config_version": "fee-depth-confidence-memory-v0",
        "max_fee_rate": d("0.020000"),
        "max_spread_cost": d("0.100000"),
        "min_depth_value": d("100.000000"),
        "min_confidence_score": d("0.600000"),
        "min_memory_observations": d("2"),
        "pass_score": d("0.750000"),
        "watch_score": d("0.450000"),
        "cost_weight": d("0.250000"),
        "depth_weight": d("0.250000"),
        "confidence_weight": d("0.250000"),
        "memory_weight": d("0.250000"),
    }
    values.update(overrides)
    return ResearchMarketFeeDepthConfidenceMemoryConfig(**values)


def observation(
    sample_index: int,
    *,
    case_id: str = "case-pass",
    fee_rate: Decimal = d("0.002000"),
    spread_cost: Decimal = d("0.020000"),
    depth_value: Decimal = d("150.000000"),
    confidence_score: Decimal = d("0.800000"),
    observed_at: datetime | None = None,
    private_candidate_ref: str | None = "candidate-alpha-secret",
    private_market_ref: str | None = "raw-market-title-secret",
    private_source_ref: str | None = "https://source.example/full?token=secret",
    private_notes: tuple[str, ...] = (
        "postgres://user:pass@host/db table=raw_events raw text block",
    ),
) -> ResearchMarketFeeDepthConfidenceMemoryObservation:
    return ResearchMarketFeeDepthConfidenceMemoryObservation(
        case_id=case_id,
        sample_id=f"sample-{sample_index:03d}",
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=sample_index)
        ),
        fee_rate=fee_rate,
        spread_cost=spread_cost,
        depth_value=depth_value,
        confidence_score=confidence_score,
        private_candidate_ref=private_candidate_ref,
        private_market_ref=private_market_ref,
        private_source_ref=private_source_ref,
        private_notes=private_notes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchMarketFeeDepthConfidenceMemoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketFeeDepthConfidenceMemoryReport:
    return build_research_market_fee_depth_confidence_memory_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_digest_payload() -> None:
    cost_report = report(())
    payload = research_market_fee_depth_confidence_memory_public_payload(cost_report)

    assert type(cost_report) is ResearchMarketFeeDepthConfidenceMemoryReport
    assert cost_report.generated_at == GENERATED_AT
    assert cost_report.segment_count == d("0")
    assert cost_report.status == "block"
    assert cost_report.reason_codes == ("no_observations",)
    assert cost_report.paper_only is True
    assert cost_report.report_only is True
    assert cost_report.readonly is True
    assert payload["segments"] == []
    assert payload["sha256_digest"] == cost_report.public_payload_sha256
    assert validate_research_market_fee_depth_confidence_memory_public_payload(payload)


def test_scores_statuses_and_digest_are_deterministic() -> None:
    rows = (
        observation(
            5,
            case_id="case-block",
            fee_rate=d("0.030000"),
            spread_cost=d("0.120000"),
            depth_value=d("10.000000"),
            confidence_score=d("0.200000"),
        ),
        observation(
            1,
            case_id="case-pass",
            fee_rate=d("0.002000"),
            spread_cost=d("0.020000"),
            depth_value=d("150.000000"),
            confidence_score=d("0.800000"),
        ),
        observation(
            2,
            case_id="case-pass",
            fee_rate=d("0.004000"),
            spread_cost=d("0.040000"),
            depth_value=d("200.000000"),
            confidence_score=d("0.900000"),
        ),
        observation(
            4,
            case_id="case-watch",
            fee_rate=d("0.010000"),
            spread_cost=d("0.050000"),
            depth_value=d("75.000000"),
            confidence_score=d("0.550000"),
        ),
    )

    cost_report = report(rows)
    same_report = report(tuple(reversed(rows)))
    payload = research_market_fee_depth_confidence_memory_public_payload(cost_report)
    same_payload = research_market_fee_depth_confidence_memory_public_payload(same_report)

    assert cost_report.status == "block"
    assert cost_report.segment_count == d("3")
    assert cost_report.pass_count == d("1")
    assert cost_report.watch_count == d("1")
    assert cost_report.block_count == d("1")
    assert cost_report.average_score == d("0.560417")
    assert tuple(row.case_id for row in cost_report.segments) == (
        "case-block",
        "case-pass",
        "case-watch",
    )

    pass_segment = cost_report.segments[1]
    assert pass_segment.status == "pass"
    assert pass_segment.observation_count == d("2")
    assert pass_segment.average_fee_rate == d("0.003000")
    assert pass_segment.average_spread_cost == d("0.030000")
    assert pass_segment.cost_score == d("0.775000")
    assert pass_segment.depth_score == d("1.000000")
    assert pass_segment.confidence_score == d("0.850000")
    assert pass_segment.memory_score == d("1.000000")
    assert pass_segment.composite_score == d("0.906250")
    assert pass_segment.reason_codes == (
        "confidence_pass",
        "cost_pass",
        "depth_pass",
        "memory_pass",
        "segment_pass",
    )

    watch_segment = cost_report.segments[2]
    assert watch_segment.status == "watch"
    assert watch_segment.composite_score == d("0.575000")
    assert "memory_watch" in watch_segment.reason_codes

    block_segment = cost_report.segments[0]
    assert block_segment.status == "block"
    assert block_segment.composite_score == d("0.200000")
    assert "cost_block" in block_segment.reason_codes

    assert payload == same_payload
    assert payload["sha256_digest"] == cost_report.public_payload_sha256
    assert len(str(payload["sha256_digest"])) == 64
    assert validate_research_market_fee_depth_confidence_memory_public_payload(payload)

    tampered = dict(payload)
    tampered["status"] = "pass"
    assert not validate_research_market_fee_depth_confidence_memory_public_payload(tampered)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_public_payload_uses_digest_labels_without_private_material() -> None:
    raw_values = (
        "candidate-alpha-secret",
        "raw-market-title-secret",
        "https://source.example/full?token=secret",
        "postgres://user:pass@host/db",
        "table=raw_events",
        "raw text block",
    )
    cost_report = report((observation(1), observation(2)))
    payload = research_market_fee_depth_confidence_memory_public_payload(cost_report)
    encoded = json.dumps(payload, sort_keys=True)

    for value in raw_values:
        assert value not in encoded

    assert tuple(payload["segments"][0]) == (
        "case_digest",
        "observation_count",
        "latest_observed_at",
        "average_fee_rate",
        "average_spread_cost",
        "average_depth_value",
        "confidence_score",
        "memory_score",
        "cost_score",
        "depth_score",
        "composite_score",
        "status",
        "reason_codes",
    )
    assert not _payload_has_private_key_fragment(payload)


def test_validation_rejects_bad_types_statuses_flags_and_digest_mismatch() -> None:
    with pytest.raises(ValueError, match="max_fee_rate"):
        config(max_fee_rate=0.02)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_fee_rate"):
        config(max_fee_rate=_DecimalSubclass("0.020000"))
    with pytest.raises(ValueError, match="pass_score"):
        config(pass_score=d("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(1),),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="fee_rate"):
        observation(1, fee_rate=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)

    good_report = report((observation(1), observation(2)))
    with pytest.raises(FrozenInstanceError):
        good_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        good_report.segments[0].composite_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(good_report.segments[0], status="blocked")
    with pytest.raises(ValueError, match="public_payload_sha256"):
        replace(good_report, public_payload_sha256="0" * 64)


def test_manual_segment_and_report_consistency_validation() -> None:
    cost_report = report((observation(1), observation(2)))
    good_segment = cost_report.segments[0]

    assert type(good_segment) is ResearchMarketFeeDepthConfidenceMemorySegment

    with pytest.raises(ValueError, match="composite_score"):
        replace(good_segment, composite_score=d("0.100000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(cost_report, pass_count=d("99"))
    with pytest.raises(ValueError, match="status"):
        replace(cost_report, status="watch")


def test_non_default_score_thresholds_validate_segment_status() -> None:
    custom_report = report(
        (observation(1), observation(2)),
        cfg=config(pass_score=d("0.950000"), watch_score=d("0.700000")),
    )
    segment = custom_report.segments[0]
    payload = research_market_fee_depth_confidence_memory_public_payload(custom_report)

    assert segment.composite_score == d("0.912500")
    assert segment.pass_score == d("0.950000")
    assert segment.watch_score == d("0.700000")
    assert segment.status == "watch"
    assert "segment_watch" in segment.reason_codes
    assert custom_report.status == "watch"
    assert validate_research_market_fee_depth_confidence_memory_public_payload(payload)


def test_owned_module_has_no_side_effect_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_fee_depth_confidence_memory_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "live trading",
        "trading",
        "sizing",
        "recommendation",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _payload_has_private_key_fragment(value: object) -> bool:
    private_fragments = (
        "candidate",
        "market",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "text",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if any(fragment in key.lower() for fragment in private_fragments):
                return True
            if _payload_has_private_key_fragment(item):
                return True
    elif isinstance(value, list):
        return any(_payload_has_private_key_fragment(item) for item in value)
    return False
