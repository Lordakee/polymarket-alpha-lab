from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import json
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_friction_explanation_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values = {
        "watch_gap_score_threshold": d("0.250000"),
        "block_gap_score_threshold": d("0.700000"),
        "spread_watch_bps": d("50.000000"),
        "spread_block_bps": d("150.000000"),
        "depth_drop_watch_ratio": d("0.250000"),
        "depth_drop_block_ratio": d("0.500000"),
        "quote_staleness_watch_seconds": d("300.000000"),
        "quote_staleness_block_seconds": d("900.000000"),
        "catalyst_watch_pressure": d("0.500000"),
        "catalyst_block_pressure": d("0.800000"),
        "fresh_evidence_seconds": d("3600.000000"),
        "stale_evidence_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return module().ResearchMarketFrictionExplanationGapConfig(**values)


def observation(
    friction_group: str = "fresh-explained-aggregate",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    aggregate_spread_bps: object = "180.000000",
    depth_drop_ratio: object = "0.650000",
    quote_staleness_seconds: object = "1200.000000",
    catalyst_pressure: object = "0.900000",
    evidence_freshness_seconds: object = "600.000000",
    explanation_count: object = "2",
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    return module().ResearchMarketFrictionExplanationGapObservation(
        friction_group=friction_group,
        observed_at=observed_at,
        aggregate_spread_bps=(
            aggregate_spread_bps
            if not isinstance(aggregate_spread_bps, str)
            else d(aggregate_spread_bps)
        ),
        depth_drop_ratio=(
            depth_drop_ratio if not isinstance(depth_drop_ratio, str) else d(depth_drop_ratio)
        ),
        quote_staleness_seconds=(
            quote_staleness_seconds
            if not isinstance(quote_staleness_seconds, str)
            else d(quote_staleness_seconds)
        ),
        catalyst_pressure=(
            catalyst_pressure
            if not isinstance(catalyst_pressure, str)
            else d(catalyst_pressure)
        ),
        evidence_freshness_seconds=(
            evidence_freshness_seconds
            if not isinstance(evidence_freshness_seconds, str)
            else d(evidence_freshness_seconds)
        ),
        explanation_count=(
            explanation_count if not isinstance(explanation_count, str) else d(explanation_count)
        ),
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows: object, cfg: object | None = None):
    return module().build_research_market_friction_explanation_gap_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def blocked_observation():
    return observation(
        "policy-surprise-aggregate",
        aggregate_spread_bps="180.000000",
        depth_drop_ratio="0.650000",
        quote_staleness_seconds="1200.000000",
        catalyst_pressure="0.900000",
        evidence_freshness_seconds="172800.000000",
        explanation_count="0",
        reason_codes=("public_catalyst_unexplained",),
    )


def watch_observation():
    return observation(
        "weather-resolution-aggregate",
        aggregate_spread_bps="75.000000",
        depth_drop_ratio="0.350000",
        quote_staleness_seconds="600.000000",
        catalyst_pressure="0.600000",
        evidence_freshness_seconds="43200.000000",
        explanation_count="1",
        reason_codes=("quote_review_needed",),
    )


def test_empty_input_returns_report_only_block_gap_report() -> None:
    gap_report = report()

    assert type(gap_report) is module().ResearchMarketFrictionExplanationGapReport
    assert is_dataclass(gap_report)
    assert gap_report.__dataclass_params__.frozen
    assert gap_report.generated_at == GENERATED_AT
    assert gap_report.config_version == (
        "research-market-friction-explanation-gap-report-v0"
    )
    assert gap_report.status == "block"
    assert gap_report.row_count == d("0")
    assert gap_report.pass_count == d("0")
    assert gap_report.watch_count == d("0")
    assert gap_report.block_count == d("0")
    assert gap_report.max_gap_score == d("0.000000")
    assert gap_report.average_gap_score is None
    assert gap_report.rows == ()
    assert gap_report.reason_codes == ("market_friction_explanation_gap_no_observations",)
    assert gap_report.reason_code_counts == (
        module().ResearchMarketFrictionExplanationGapReasonCodeCount(
            reason_code="market_friction_explanation_gap_no_observations",
            count=d("1"),
        ),
    )
    assert gap_report.paper_only is True
    assert gap_report.report_only is True
    assert gap_report.readonly is True


def test_friction_pressure_without_fresh_explanations_blocks_or_watches() -> None:
    gap_report = report(
        watch_observation(),
        observation("fresh-explained-aggregate"),
        blocked_observation(),
    )

    assert gap_report.status == "block"
    assert gap_report.row_count == d("3")
    assert gap_report.block_count == d("1")
    assert gap_report.watch_count == d("1")
    assert gap_report.pass_count == d("1")
    assert gap_report.max_gap_score == d("1.000000")
    assert gap_report.average_gap_score == d("0.428986")
    assert tuple(row.friction_group for row in gap_report.rows) == (
        "policy-surprise-aggregate",
        "weather-resolution-aggregate",
        "fresh-explained-aggregate",
    )

    blocked, watched, passed = gap_report.rows
    assert blocked.status == "block"
    assert blocked.spread_pressure_score == d("1.000000")
    assert blocked.depth_pressure_score == d("1.000000")
    assert blocked.quote_staleness_pressure_score == d("1.000000")
    assert blocked.friction_pressure_score == d("1.000000")
    assert blocked.evidence_gap_score == d("1.000000")
    assert blocked.gap_score == d("1.000000")
    assert blocked.reason_codes == (
        "aggregate_spread_block",
        "catalyst_pressure_block",
        "depth_drop_block",
        "evidence_stale",
        "explanation_gap_block",
        "input_public_catalyst_unexplained",
        "missing_explanations",
        "quote_staleness_block",
    )

    assert watched.status == "watch"
    assert watched.spread_pressure_score == d("0.250000")
    assert watched.depth_pressure_score == d("0.400000")
    assert watched.quote_staleness_pressure_score == d("0.500000")
    assert watched.friction_pressure_score == d("0.600000")
    assert watched.evidence_gap_score == d("0.478261")
    assert watched.gap_score == d("0.286957")
    assert watched.reason_codes == (
        "aggregate_spread_watch",
        "catalyst_pressure_watch",
        "depth_drop_watch",
        "evidence_stale",
        "explanation_gap_watch",
        "explanations_present",
        "input_quote_review_needed",
        "quote_staleness_watch",
    )

    assert passed.status == "pass"
    assert passed.gap_score == d("0.000000")
    assert passed.reason_codes == (
        "aggregate_spread_block",
        "catalyst_pressure_block",
        "depth_drop_block",
        "evidence_fresh",
        "explanation_gap_pass",
        "explanations_present",
        "quote_staleness_block",
    )


def test_payload_and_digest_are_deterministic_public_safe_and_float_free() -> None:
    forward = report(blocked_observation(), watch_observation())
    reverse = report(watch_observation(), blocked_observation())

    assert forward == reverse

    payload = module().research_market_friction_explanation_gap_report_payload(forward)
    digest = module().research_market_friction_explanation_gap_report_digest(forward)

    assert digest == module().research_market_friction_explanation_gap_report_digest(reverse)
    assert len(digest) == 64
    int(digest, 16)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["row_count"] == "2"
    assert payload["rows"][0]["aggregate_spread_bps"] == "180.000000"
    assert payload["rows"][1]["gap_score"] == "0.286957"
    json.dumps(payload, sort_keys=True)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(payload))
    assert not any(isinstance(value, datetime) for value in _walk_payload_values(payload))

    encoded = json.dumps(payload, sort_keys=True)
    forbidden_fragments = (
        "market_slug",
        "market_id",
        "condition_id",
        "source_id",
        "source_url",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "sizing",
        "recommendation",
        "live_execution",
    )
    assert all(fragment not in encoded.lower() for fragment in forbidden_fragments)


def test_validation_rejects_bad_types_unsafe_identifiers_flags_and_inconsistency() -> None:
    good_row = observation("validation-aggregate")
    gap_report = report(good_row)

    with pytest.raises(FrozenInstanceError):
        good_row.friction_group = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gap_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gap_report.reason_code_counts[0].count = d("2")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadObservation",
            (module().ResearchMarketFrictionExplanationGapObservation,),
            {},
        )
    with pytest.raises(ValueError, match="aggregate_spread_bps"):
        observation(aggregate_spread_bps=_DecimalSubclass("12.000000"))
    with pytest.raises(ValueError, match="depth_drop_ratio"):
        observation(depth_drop_ratio=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        module().build_research_market_friction_explanation_gap_report(
            (good_row,),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="friction_group"):
        observation("market_slug:event-123")
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        observation("bad-flags", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="watch_gap_score_threshold"):
        config(watch_gap_score_threshold=d("0.800000"))
    with pytest.raises(ValueError, match="spread_block_bps"):
        config(spread_watch_bps=d("150.000000"), spread_block_bps=d("100.000000"))
    with pytest.raises(ValueError, match="duplicate friction_group"):
        report(observation("dupe-aggregate"), observation("dupe-aggregate"))
    with pytest.raises(ValueError, match="status"):
        replace(gap_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="gap_score"):
        replace(gap_report.rows[0], gap_score=d("0.750000"))


def test_public_records_are_frozen_and_expose_only_exact_decimal_values() -> None:
    gap_report = report(blocked_observation(), watch_observation())

    for public_record in (
        config(),
        blocked_observation(),
        gap_report.rows[0],
        gap_report.reason_code_counts[0],
        gap_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name


def test_module_has_no_side_effect_trading_or_live_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_friction_explanation_gap_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "sizing",
        "recommendation",
        "private_key",
        "live_execution",
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
