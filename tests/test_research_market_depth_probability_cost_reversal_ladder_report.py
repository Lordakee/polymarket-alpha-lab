from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_depth_probability_cost_reversal_ladder_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_COST_REVERSAL_LADDER_REPORT_CONFIG_VERSION
        ),
        "probability_reversal_watch_threshold": d("0.100000"),
        "probability_reversal_block_threshold": d("0.250000"),
        "min_pass_depth": d("1000.000000"),
        "min_watch_depth": d("250.000000"),
        "max_pass_cost_ratio": d("0.025000"),
        "max_watch_cost_ratio": d("0.075000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthProbabilityCostReversalLadderConfig(**values)


def ladder_input(
    public_ladder_ref: str = "ladder-pass",
    *,
    observed_at: datetime | None = None,
    prior_probability: Decimal = d("0.500000"),
    current_probability: Decimal = d("0.540000"),
    available_depth: Decimal = d("1500.000000"),
    fee_ratio: Decimal = d("0.005000"),
    spread_ratio: Decimal = d("0.005000"),
    impact_ratio: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketDepthProbabilityCostReversalLadderInput(
        public_ladder_ref=public_ladder_ref,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(seconds=30)
        ),
        prior_probability=prior_probability,
        current_probability=current_probability,
        available_depth=available_depth,
        fee_ratio=fee_ratio,
        spread_ratio=spread_ratio,
        impact_ratio=impact_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_depth_probability_cost_reversal_ladder_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_builds_depth_probability_cost_reversal_ladder_rollups() -> None:
    module = api()

    combined = report(
        ladder_input(
            "ladder-pass",
            reason_codes=("manual_context",),
        ),
        ladder_input(
            "ladder-block",
            prior_probability=d("0.700000"),
            current_probability=d("0.400000"),
            available_depth=d("100.000000"),
            fee_ratio=d("0.050000"),
            spread_ratio=d("0.030000"),
            impact_ratio=d("0.010000"),
        ),
        ladder_input(
            "ladder-watch",
            prior_probability=d("0.500000"),
            current_probability=d("0.620000"),
            available_depth=d("800.000000"),
            fee_ratio=d("0.020000"),
            spread_ratio=d("0.010000"),
            impact_ratio=d("0.005000"),
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert type(combined) is module.ResearchMarketDepthProbabilityCostReversalLadderReport
    assert is_dataclass(combined)
    assert combined.status == "block"
    assert combined.input_count == d("3.000000")
    assert combined.row_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.average_ladder_risk_score == d("0.422222")
    assert combined.max_ladder_risk_score == d("1.000000")
    assert combined.max_probability_reversal == d("0.300000")
    assert combined.max_total_cost_ratio == d("0.090000")
    assert combined.min_available_depth == d("100.000000")
    assert combined.reason_codes == (
        "probability_reversal_block",
        "depth_floor_block",
        "cost_drag_block",
        "probability_reversal_watch",
        "depth_floor_watch",
        "cost_drag_watch",
        "depth_probability_cost_ladder_pass",
        "input_manual_context",
    )
    assert tuple(row.public_ladder_ref for row in combined.rows) == (
        "ladder-block",
        "ladder-watch",
        "ladder-pass",
    )

    block_row, watch_row, pass_row = combined.rows
    assert block_row.probability_reversal == d("0.300000")
    assert block_row.total_cost_ratio == d("0.090000")
    assert block_row.probability_reversal_score == d("1.000000")
    assert block_row.depth_risk_score == d("1.000000")
    assert block_row.cost_risk_score == d("1.000000")
    assert block_row.ladder_risk_score == d("1.000000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "probability_reversal_block",
        "depth_floor_block",
        "cost_drag_block",
    )

    assert watch_row.probability_reversal == d("0.120000")
    assert watch_row.total_cost_ratio == d("0.035000")
    assert watch_row.probability_reversal_score == d("0.133333")
    assert watch_row.depth_risk_score == d("0.266667")
    assert watch_row.cost_risk_score == d("0.200000")
    assert watch_row.ladder_risk_score == d("0.266667")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "probability_reversal_watch",
        "depth_floor_watch",
        "cost_drag_watch",
    )

    assert pass_row.status == "pass"
    assert pass_row.ladder_risk_score == d("0.000000")
    assert pass_row.reason_codes == (
        "depth_probability_cost_ladder_pass",
        "input_manual_context",
    )


def test_empty_report_blocks_with_decimal_zero_rollups() -> None:
    module = api()
    empty = report()

    assert empty.status == "block"
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.average_ladder_risk_score == d("0.000000")
    assert empty.reason_codes == ("no_depth_probability_cost_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount(
            reason_code="no_depth_probability_cost_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert empty.rows == ()


def test_input_reason_codes_do_not_escalate_computed_status() -> None:
    combined = report(
        ladder_input(
            reason_codes=("manual_block", "manual_watch"),
        ),
    )

    assert combined.status == "pass"
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("0.000000")
    assert combined.block_count == d("0.000000")
    assert combined.rows[0].status == "pass"
    assert combined.rows[0].reason_codes == (
        "depth_probability_cost_ladder_pass",
        "input_manual_block",
        "input_manual_watch",
    )


def test_payload_is_deterministic_safe_json_and_digest_validated() -> None:
    module = api()
    left = report(ladder_input("ladder-b"), ladder_input("ladder-a"))
    right = report(ladder_input("ladder-a"), ladder_input("ladder-b"))

    left_payload = module.research_market_depth_probability_cost_reversal_ladder_report_payload(
        left,
    )
    right_payload = module.research_market_depth_probability_cost_reversal_ladder_report_payload(
        right,
    )

    assert left_payload == right_payload
    json.dumps(left_payload, sort_keys=True)
    assert left_payload["generated_at"] == "2026-07-09T15:00:00+00:00"
    assert left_payload["input_count"] == "2.000000"
    assert left_payload["rows"][0]["public_ladder_ref"] == "ladder-a"
    assert left_payload["rows"][0]["prior_probability"] == "0.500000"
    assert left_payload["rows"][0]["total_cost_ratio"] == "0.010000"
    assert left_payload["paper_only"] is True
    assert left_payload["report_only"] is True
    assert left_payload["readonly"] is True
    assert len(left.derived_validation_digest) == 64
    int(left.derived_validation_digest, 16)
    assert left_payload["derived_validation_digest"] == left.derived_validation_digest

    without_digest = dict(left_payload)
    without_digest.pop("derived_validation_digest")
    canonical = json.dumps(
        without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == (
        left.derived_validation_digest
    )
    assert not any(isinstance(value, float) for value in walk_payload_values(left_payload))
    assert not any(type(value) is int for value in walk_payload_values(left_payload))
    _assert_no_forbidden_public_leakage(left_payload)

    assert module.research_market_depth_probability_cost_reversal_ladder_report_digest(
        left,
    ) == left.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(left, derived_validation_digest="0" * 64)

    tampered_payload = dict(left_payload)
    tampered_payload["public_note"] = "safe_public_note"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_depth_probability_cost_reversal_ladder_report_payload(
            tampered_payload,
        )

    malformed_payload = dict(left_payload)
    malformed_payload["derived_validation_digest"] = "not-a-sha256"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_depth_probability_cost_reversal_ladder_report_payload(
            malformed_payload,
        )


def test_validates_decimal_exactness_dates_flags_and_status_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="prior_probability"):
        ladder_input(prior_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="prior_probability"):
        ladder_input(prior_probability=d("NaN"))
    with pytest.raises(ValueError, match="current_probability"):
        ladder_input(current_probability=DecimalSubclass("0.510000"))
    with pytest.raises(ValueError, match="available_depth"):
        ladder_input(available_depth=d("Infinity"))
    with pytest.raises(ValueError, match="fee_ratio"):
        ladder_input(fee_ratio=d("-0.000001"))
    with pytest.raises(ValueError, match="observed_at"):
        ladder_input(observed_at=datetime(2026, 7, 9, 14, 59))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            ladder_input(),
            generated_at=DatetimeSubclass(2026, 7, 9, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="probability_reversal_watch_threshold"):
        config(probability_reversal_watch_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="min_pass_depth"):
        config(min_pass_depth=d("100.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ladder_input(report_only=False)

    good = report(ladder_input())
    with pytest.raises(ValueError, match="readonly"):
        replace(good, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(good.rows[0], status="ready")
    with pytest.raises(FrozenInstanceError):
        good.rows[0].ladder_risk_score = d("0.000000")  # type: ignore[misc]

    for value in (config(), ladder_input(), good.rows[0], good.reason_code_counts[0], good):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    assert all(field.default is True for field in fields(config())[-3:])
    assert all(field.default is True for field in fields(good.rows[0])[-3:])
    assert all(field.default is True for field in fields(good)[-3:])
    assert set(module.STATUSES) == {"pass", "watch", "block"}


def test_rejects_public_identifier_and_payload_leakage_surfaces() -> None:
    module = api()

    for unsafe_value in (
        "candidate-123",
        "market_id_abc",
        "market-slug-abc",
        "source_url_abc",
        "question-will-this-happen",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            ladder_input(public_ladder_ref=unsafe_value)

    for unsafe_codes in (
        ("source_text",),
        ("wallet_pressure",),
        ("order_flow",),
        ("table_name",),
        ("token_seen",),
    ):
        with pytest.raises(ValueError, match="unsafe"):
            ladder_input(reason_codes=unsafe_codes)

    good = report(ladder_input())
    payload = module.research_market_depth_probability_cost_reversal_ladder_report_payload(
        good,
    )
    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_depth_probability_cost_reversal_ladder_report_payload(
            unsafe_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["public_note"] = "source_text leaked"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_depth_probability_cost_reversal_ladder_report_payload(
            unsafe_payload,
        )

    for unsafe_key in (
        "marketId",
        "marketSlug",
        "sourceUrl",
        "sourceText",
        "tableName",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "abc"
        with pytest.raises(ValueError, match="unsafe"):
            module.research_market_depth_probability_cost_reversal_ladder_report_payload(
                unsafe_payload,
            )

    for unsafe_value in (
        "market id leaked",
        "market slug leaked",
        "source-url leaked",
        "source text leaked",
        "table-name leaked",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload["public_note"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe"):
            module.research_market_depth_probability_cost_reversal_ladder_report_payload(
                unsafe_payload,
            )


def test_owned_module_has_no_external_execution_storage_or_decision_surface() -> None:
    module = api()
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_probability_cost_reversal_ladder_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "network",
        "live trading",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "raw_candidate",
    )

    assert all(term not in source for term in forbidden_terms)
    assert not any(
        term in public_name.lower()
        for public_name in module.__all__
        for term in forbidden_terms
    )
    for cls in (
        module.ResearchMarketDepthProbabilityCostReversalLadderConfig,
        module.ResearchMarketDepthProbabilityCostReversalLadderInput,
        module.ResearchMarketDepthProbabilityCostReversalLadderRow,
        module.ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount,
        module.ResearchMarketDepthProbabilityCostReversalLadderReport,
    ):
        for field in fields(cls):
            assert not any(term in field.name.lower() for term in forbidden_terms)


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _assert_no_forbidden_public_leakage(value: object) -> None:
    forbidden_fragments = (
        "candidate",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "network",
        "live trading",
        "://",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(term in lowered_key for term in forbidden_fragments)
            _assert_no_forbidden_public_leakage(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_forbidden_public_leakage(item)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        assert not any(term in lowered_value for term in forbidden_fragments)
