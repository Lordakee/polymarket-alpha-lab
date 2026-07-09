from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_memory_fee_depth_guard_report import (
    ResearchMarketMemoryFeeDepthGuardConfig,
    ResearchMarketMemoryFeeDepthGuardObservation,
    ResearchMarketMemoryFeeDepthGuardReport,
    ResearchMarketMemoryFeeDepthGuardRow,
    build_research_market_memory_fee_depth_guard_report,
    research_market_memory_fee_depth_guard_public_payload,
    validate_research_market_memory_fee_depth_guard_public_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketMemoryFeeDepthGuardConfig:
    values = {
        "config_version": "memory-fee-depth-guard-v0",
        "max_fee_rate": d("0.020000"),
        "max_spread_cost": d("0.100000"),
        "min_depth_value": d("100.000000"),
        "min_memory_observations": d("2"),
        "pass_score": d("0.750000"),
        "watch_score": d("0.450000"),
        "cost_weight": d("0.333333"),
        "depth_weight": d("0.333333"),
        "memory_weight": d("0.333334"),
    }
    values.update(overrides)
    return ResearchMarketMemoryFeeDepthGuardConfig(**values)


def observation(
    sample_index: int,
    *,
    case_id: str = "case-pass",
    fee_rate: Decimal = d("0.002000"),
    spread_cost: Decimal = d("0.020000"),
    depth_value: Decimal = d("150.000000"),
    observed_at: datetime | None = None,
    private_refs: tuple[str, ...] = (
        "candidate-alpha-secret",
        "raw-market-title-secret",
        "https://source.example/full?token=secret",
        "postgres://user:pass@host/db dsn=main table=raw_events",
        "raw text block",
    ),
) -> ResearchMarketMemoryFeeDepthGuardObservation:
    return ResearchMarketMemoryFeeDepthGuardObservation(
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
        private_refs=private_refs,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchMarketMemoryFeeDepthGuardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketMemoryFeeDepthGuardReport:
    return build_research_market_memory_fee_depth_guard_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_digest_payload() -> None:
    guard_report = report(())
    payload = research_market_memory_fee_depth_guard_public_payload(guard_report)

    assert type(guard_report) is ResearchMarketMemoryFeeDepthGuardReport
    assert guard_report.generated_at == GENERATED_AT
    assert guard_report.item_count == d("0")
    assert guard_report.status == "block"
    assert guard_report.reason_codes == ("no_observations",)
    assert guard_report.paper_only is True
    assert guard_report.report_only is True
    assert guard_report.readonly is True
    assert payload["rows"] == []
    assert payload["sha256_digest"] == guard_report.public_payload_sha256
    assert validate_research_market_memory_fee_depth_guard_public_payload(payload)
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))


def test_scores_statuses_and_digest_are_deterministic_without_private_leakage() -> None:
    rows = (
        observation(
            5,
            case_id="case-block",
            fee_rate=d("0.030000"),
            spread_cost=d("0.120000"),
            depth_value=d("10.000000"),
        ),
        observation(
            1,
            case_id="case-pass",
            fee_rate=d("0.002000"),
            spread_cost=d("0.020000"),
            depth_value=d("150.000000"),
        ),
        observation(
            2,
            case_id="case-pass",
            fee_rate=d("0.004000"),
            spread_cost=d("0.040000"),
            depth_value=d("200.000000"),
        ),
        observation(
            4,
            case_id="case-watch",
            fee_rate=d("0.010000"),
            spread_cost=d("0.050000"),
            depth_value=d("75.000000"),
        ),
    )

    guard_report = report(rows)
    same_report = report(tuple(reversed(rows)))
    payload = research_market_memory_fee_depth_guard_public_payload(guard_report)
    same_payload = research_market_memory_fee_depth_guard_public_payload(same_report)

    assert guard_report.status == "block"
    assert guard_report.item_count == d("3")
    assert guard_report.pass_count == d("1")
    assert guard_report.watch_count == d("1")
    assert guard_report.block_count == d("1")
    assert guard_report.average_guard_score == d("0.569444")
    assert tuple(row.status for row in guard_report.rows) == ("block", "watch", "pass")

    block_row, watch_row, pass_row = guard_report.rows
    assert block_row.guard_score == d("0.200000")
    assert block_row.reason_codes == (
        "cost_block",
        "depth_block",
        "guard_block",
        "memory_watch",
    )
    assert watch_row.guard_score == d("0.583333")
    assert "guard_watch" in watch_row.reason_codes
    assert pass_row.observation_count == d("2")
    assert pass_row.average_fee_rate == d("0.003000")
    assert pass_row.average_spread_cost == d("0.030000")
    assert pass_row.cost_score == d("0.775000")
    assert pass_row.depth_score == d("1.000000")
    assert pass_row.memory_score == d("1.000000")
    assert pass_row.guard_score == d("0.925000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "cost_pass",
        "depth_pass",
        "guard_pass",
        "memory_pass",
    )

    assert payload == same_payload
    assert payload["sha256_digest"] == guard_report.public_payload_sha256
    assert len(str(payload["sha256_digest"])) == 64
    assert validate_research_market_memory_fee_depth_guard_public_payload(payload)

    encoded = json.dumps(payload, sort_keys=True)
    for value in (
        "candidate-alpha-secret",
        "raw-market-title-secret",
        "https://source.example/full?token=secret",
        "postgres://user:pass@host/db",
        "dsn=main",
        "table=raw_events",
        "raw text block",
    ):
        assert value not in encoded
    assert not _payload_has_private_key_or_value_fragment(payload)

    tampered = dict(payload)
    tampered["status"] = "pass"
    assert not validate_research_market_memory_fee_depth_guard_public_payload(tampered)


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
        good_report.rows[0].guard_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(good_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="public_payload_sha256"):
        replace(good_report, public_payload_sha256="0" * 64)


def test_manual_row_and_report_consistency_validation() -> None:
    guard_report = report((observation(1), observation(2)))
    good_row = guard_report.rows[0]

    assert type(good_row) is ResearchMarketMemoryFeeDepthGuardRow

    with pytest.raises(ValueError, match="guard_score"):
        replace(good_row, guard_score=d("0.100000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(guard_report, pass_count=d("99"))
    with pytest.raises(ValueError, match="status"):
        replace(guard_report, status="watch")


def test_owned_module_has_no_side_effect_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_memory_fee_depth_guard_report.py"
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


def _payload_has_private_key_or_value_fragment(value: object) -> bool:
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
            if _payload_has_private_key_or_value_fragment(item):
                return True
    elif isinstance(value, list):
        return any(_payload_has_private_key_or_value_fragment(item) for item in value)
    elif isinstance(value, str):
        return any(fragment in value.lower() for fragment in private_fragments)
    return False
