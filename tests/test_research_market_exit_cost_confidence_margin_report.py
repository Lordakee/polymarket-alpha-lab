from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 30, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_exit_cost_confidence_margin_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_exit_cost_confidence_margin_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_EXIT_COST_CONFIDENCE_MARGIN_REPORT_CONFIG_VERSION
        ),
        "pass_min_confidence_score": d("0.750000"),
        "watch_min_confidence_score": d("0.550000"),
        "pass_max_exit_cost_rate": d("0.030000"),
        "block_max_exit_cost_rate": d("0.080000"),
        "pass_min_confidence_margin": d("0.720000"),
        "block_min_confidence_margin": d("0.500000"),
        "liquidity_buffer_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchMarketExitCostConfidenceMarginConfig(**values)


def observation(
    internal_research_ref: str,
    *,
    exit_fee_rate: Decimal,
    exit_spread_rate: Decimal,
    exit_slippage_rate: Decimal,
    liquidity_confidence_score: Decimal,
    evidence_confidence_score: Decimal,
    resolution_confidence_score: Decimal,
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketExitCostConfidenceMarginObservation(
        internal_research_ref=internal_research_ref,
        observed_at=observed_at,
        exit_fee_rate=exit_fee_rate,
        exit_spread_rate=exit_spread_rate,
        exit_slippage_rate=exit_slippage_rate,
        liquidity_confidence_score=liquidity_confidence_score,
        evidence_confidence_score=evidence_confidence_score,
        resolution_confidence_score=resolution_confidence_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations: object, cfg: object | None = None):
    module = api()
    return module.build_research_market_exit_cost_confidence_margin_report(
        observations,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def walk_payload(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from walk_payload(item)
        return
    yield value


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def payload_with_recomputed_digest(payload: dict[str, object]) -> dict[str, object]:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return dict(
        digest_payload,
        derived_validation_digest=hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
    )


def test_exit_cost_confidence_margin_scores_sorts_and_aggregates_statuses() -> None:
    module = api()
    result = build_report(
        observation(
            "private-pass candidate-id market-id market-slug question https://example.invalid",
            exit_fee_rate=d("0.006000"),
            exit_spread_rate=d("0.010000"),
            exit_slippage_rate=d("0.004000"),
            liquidity_confidence_score=d("0.900000"),
            evidence_confidence_score=d("0.820000"),
            resolution_confidence_score=d("0.880000"),
        ),
        observation(
            "private-block dsn=postgres table=events token=secret wallet order trade",
            exit_fee_rate=d("0.040000"),
            exit_spread_rate=d("0.030000"),
            exit_slippage_rate=d("0.020000"),
            liquidity_confidence_score=d("0.700000"),
            evidence_confidence_score=d("0.400000"),
            resolution_confidence_score=d("0.500000"),
            reason_codes=("needs_evidence_review",),
        ),
        observation(
            "private-watch raw question source_url=https://example.invalid source_text=secret",
            exit_fee_rate=d("0.010000"),
            exit_spread_rate=d("0.015000"),
            exit_slippage_rate=d("0.005000"),
            liquidity_confidence_score=d("0.800000"),
            evidence_confidence_score=d("0.650000"),
            resolution_confidence_score=d("0.750000"),
        ),
    )

    assert module.MARKET_EXIT_COST_CONFIDENCE_MARGIN_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert type(result) is module.ResearchMarketExitCostConfidenceMarginReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.observation_count == d("3.000000")
    assert result.pass_count == ONE
    assert result.watch_count == ONE
    assert result.block_count == ONE
    assert result.max_exit_cost_rate == d("0.105000")
    assert result.min_confidence_margin == d("0.428333")
    assert result.average_exit_cost_rate == d("0.056667")
    assert result.average_confidence_score == d("0.711111")
    assert result.average_confidence_margin == d("0.654444")
    assert result.status == "block"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    block_row, watch_row, pass_row = result.rows
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.public_row_ref for row in result.rows) == (
        "exit_cost_confidence_margin_row_001",
        "exit_cost_confidence_margin_row_002",
        "exit_cost_confidence_margin_row_003",
    )
    assert block_row.total_exit_cost_rate == d("0.105000")
    assert block_row.confidence_score == d("0.533333")
    assert block_row.confidence_margin == d("0.428333")
    assert block_row.reason_codes == (
        "confidence_margin_block",
        "confidence_score_below_watch_band",
        "exit_cost_above_block_band",
        "input_needs_evidence_review",
        "liquidity_buffer_applied",
    )
    assert watch_row.total_exit_cost_rate == d("0.040000")
    assert watch_row.confidence_margin == d("0.693333")
    assert watch_row.reason_codes == (
        "confidence_margin_watch",
        "confidence_score_watch_band",
        "exit_cost_watch_band",
        "liquidity_buffer_applied",
    )
    assert pass_row.total_exit_cost_rate == d("0.025000")
    assert pass_row.confidence_margin == d("0.841667")
    assert pass_row.reason_codes == (
        "confidence_margin_pass",
        "confidence_score_high",
        "exit_cost_within_pass_band",
        "liquidity_buffer_applied",
    )
    assert_digest(block_row.row_validation_digest)
    assert_digest(result.derived_validation_digest)


def test_exit_cost_above_block_band_forces_report_block_status() -> None:
    result = build_report(
        observation(
            "internal-high-exit-cost",
            exit_fee_rate=d("0.070000"),
            exit_spread_rate=d("0.010000"),
            exit_slippage_rate=d("0.000000"),
            liquidity_confidence_score=d("1.000000"),
            evidence_confidence_score=d("1.000000"),
            resolution_confidence_score=d("1.000000"),
        ),
    )

    assert result.rows[0].status == "block"
    assert result.rows[0].reason_codes == (
        "confidence_margin_pass",
        "confidence_score_high",
        "exit_cost_above_block_band",
    )
    assert result.status == "block"


def test_public_payload_is_deterministic_digest_bound_decimal_only_and_safe() -> None:
    module = api()
    private_ref = (
        "candidate-alpha market-id market-slug raw question text "
        "https://example.invalid source_url=https://example.invalid "
        "source_text=secret dsn=postgres table=events token=secret wallet order trade"
    )
    first = build_report(
        observation(
            private_ref,
            exit_fee_rate=d("0.040000"),
            exit_spread_rate=d("0.030000"),
            exit_slippage_rate=d("0.020000"),
            liquidity_confidence_score=d("0.700000"),
            evidence_confidence_score=d("0.400000"),
            resolution_confidence_score=d("0.500000"),
        ),
    )
    second = build_report(
        observation(
            private_ref,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            exit_fee_rate=d("0.040000"),
            exit_spread_rate=d("0.030000"),
            exit_slippage_rate=d("0.020000"),
            liquidity_confidence_score=d("0.700000"),
            evidence_confidence_score=d("0.400000"),
            resolution_confidence_score=d("0.500000"),
        ),
    )

    payload = module.research_market_exit_cost_confidence_margin_report_payload(first)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    encoded_digest_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    encoded_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload == module.research_market_exit_cost_confidence_margin_report_payload(
        second,
    )
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.research_market_exit_cost_confidence_margin_report_digest(first) == (
        first.derived_validation_digest
    )
    assert hashlib.sha256(encoded_digest_payload.encode("utf-8")).hexdigest() == (
        first.derived_validation_digest
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["rows"][0]["total_exit_cost_rate"] == "0.105000"
    assert payload["rows"][0]["internal_research_ref_digest"] == (
        first.rows[0].internal_research_ref_digest
    )
    assert private_ref not in encoded_payload
    assert all(
        fragment not in encoded_payload.lower()
        for fragment in (
            "candidate-alpha",
            "candidate_id",
            "market-id",
            "market_id",
            "market-slug",
            "market_slug",
            "raw question",
            "source_url",
            "source_text",
            "https://example.invalid",
            "dsn=postgres",
            "table=events",
            "token=secret",
            "wallet",
            "order",
            "trade",
            "live",
            "recommend",
            "sizing",
        )
    )
    assert not any(type(value) in (float, int) for value in walk_payload(payload))


def test_empty_input_blocks_without_public_private_reference_surface() -> None:
    result = build_report()

    assert result.observation_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.max_exit_cost_rate == ZERO
    assert result.min_confidence_margin == ZERO
    assert result.average_exit_cost_rate is None
    assert result.average_confidence_score is None
    assert result.average_confidence_margin is None
    assert result.status == "block"
    assert result.rows == ()
    assert result.reason_codes == ("missing_exit_cost_confidence_margin_observations",)
    assert_digest(result.derived_validation_digest)


def test_validation_enforces_frozen_decimal_only_flags_and_digest_contract() -> None:
    module = api()
    result = build_report(
        observation(
            "internal-alpha",
            exit_fee_rate=d("0.006000"),
            exit_spread_rate=d("0.010000"),
            exit_slippage_rate=d("0.004000"),
            liquidity_confidence_score=d("0.900000"),
            evidence_confidence_score=d("0.820000"),
            resolution_confidence_score=d("0.880000"),
        ),
    )

    assert is_dataclass(module.ResearchMarketExitCostConfidenceMarginConfig)
    assert is_dataclass(module.ResearchMarketExitCostConfidenceMarginObservation)
    assert is_dataclass(module.ResearchMarketExitCostConfidenceMarginRow)
    assert is_dataclass(module.ResearchMarketExitCostConfidenceMarginReasonCodeCount)
    assert is_dataclass(module.ResearchMarketExitCostConfidenceMarginReport)
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(
            "internal-flags",
            exit_fee_rate=d("0.006000"),
            exit_spread_rate=d("0.010000"),
            exit_slippage_rate=d("0.004000"),
            liquidity_confidence_score=d("0.900000"),
            evidence_confidence_score=d("0.820000"),
            resolution_confidence_score=d("0.880000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="exit_fee_rate"):
        observation(
            "internal-decimal",
            exit_fee_rate=0,  # type: ignore[arg-type]
            exit_spread_rate=d("0.010000"),
            exit_slippage_rate=d("0.004000"),
            liquidity_confidence_score=d("0.900000"),
            evidence_confidence_score=d("0.820000"),
            resolution_confidence_score=d("0.880000"),
        )
    with pytest.raises(ValueError, match="exit_spread_rate"):
        observation(
            "internal-decimal-subclass",
            exit_fee_rate=d("0.006000"),
            exit_spread_rate=_DecimalSubclass("0.010000"),
            exit_slippage_rate=d("0.004000"),
            liquidity_confidence_score=d("0.900000"),
            evidence_confidence_score=d("0.820000"),
            resolution_confidence_score=d("0.880000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_exit_cost_confidence_margin_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_exit_cost_confidence_margin_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="internal_research_ref values"):
        build_report(
            observation(
                "internal-dupe",
                exit_fee_rate=d("0.006000"),
                exit_spread_rate=d("0.010000"),
                exit_slippage_rate=d("0.004000"),
                liquidity_confidence_score=d("0.900000"),
                evidence_confidence_score=d("0.820000"),
                resolution_confidence_score=d("0.880000"),
            ),
            observation(
                "internal-dupe",
                exit_fee_rate=d("0.006000"),
                exit_spread_rate=d("0.010000"),
                exit_slippage_rate=d("0.004000"),
                liquidity_confidence_score=d("0.900000"),
                evidence_confidence_score=d("0.820000"),
                resolution_confidence_score=d("0.880000"),
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="halt")
    with pytest.raises(ValueError, match="row_validation_digest"):
        replace(result.rows[0], row_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_min_confidence_score"):
        config(pass_min_confidence_score=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="block_max_exit_cost_rate"):
        config(block_max_exit_cost_rate=d("0.020000"))


def test_payload_validation_rejects_tampering_numeric_literals_and_unsafe_surfaces() -> None:
    module = api()
    payload = module.research_market_exit_cost_confidence_margin_report_payload(
        build_report(
            observation(
                "internal-alpha",
                exit_fee_rate=d("0.006000"),
                exit_spread_rate=d("0.010000"),
                exit_slippage_rate=d("0.004000"),
                liquidity_confidence_score=d("0.900000"),
                evidence_confidence_score=d("0.820000"),
                resolution_confidence_score=d("0.880000"),
            ),
        ),
    )

    assert module.research_market_exit_cost_confidence_margin_report_payload(payload) == (
        payload
    )
    tampered = dict(payload, pass_count="0.000000")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_exit_cost_confidence_margin_report_payload(tampered)

    unsafe_key = dict(payload)
    unsafe_key["wallet_address"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_exit_cost_confidence_margin_report_payload(unsafe_key)

    numeric_literal = dict(payload, observation_count=1)
    with pytest.raises(ValueError, match="Decimal-derived string"):
        module.research_market_exit_cost_confidence_margin_report_payload(numeric_literal)

    invalid_status = payload_with_recomputed_digest(dict(payload, status="halt"))
    with pytest.raises(ValueError, match="status"):
        module.research_market_exit_cost_confidence_margin_report_payload(invalid_status)

    invalid_nested_flag = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
    invalid_nested_flag["rows"][0]["readonly"] = False
    invalid_nested_flag = payload_with_recomputed_digest(invalid_nested_flag)
    with pytest.raises(ValueError, match="readonly"):
        module.research_market_exit_cost_confidence_margin_report_payload(
            invalid_nested_flag,
        )


def test_owned_module_has_no_runtime_side_effect_or_action_surface() -> None:
    module = api()
    module_text = MODULE_PATH.read_text(encoding="utf-8").lower()
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
        "trade",
        "live",
        "recommendation",
        "sizing",
    )

    assert module.__all__ == (
        "MARKET_EXIT_COST_CONFIDENCE_MARGIN_STATUSES",
        "DEFAULT_RESEARCH_MARKET_EXIT_COST_CONFIDENCE_MARGIN_REPORT_CONFIG_VERSION",
        "ResearchMarketExitCostConfidenceMarginConfig",
        "ResearchMarketExitCostConfidenceMarginObservation",
        "ResearchMarketExitCostConfidenceMarginReasonCodeCount",
        "ResearchMarketExitCostConfidenceMarginReport",
        "ResearchMarketExitCostConfidenceMarginRow",
        "build_research_market_exit_cost_confidence_margin_report",
        "research_market_exit_cost_confidence_margin_report_digest",
        "research_market_exit_cost_confidence_margin_report_payload",
    )
    assert all(term not in module_text for term in forbidden_terms)
