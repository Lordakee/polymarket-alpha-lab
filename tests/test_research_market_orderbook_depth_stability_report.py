from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 21, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_orderbook_depth_stability_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_ORDERBOOK_DEPTH_STABILITY_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_depth_coverage_ratio": d("0.800000"),
        "minimum_watch_depth_coverage_ratio": d("0.500000"),
        "maximum_pass_spread_instability_ratio": d("0.100000"),
        "maximum_watch_spread_instability_ratio": d("0.300000"),
        "maximum_pass_imbalance_volatility_ratio": d("0.100000"),
        "maximum_watch_imbalance_volatility_ratio": d("0.250000"),
        "maximum_pass_liquidity_age_seconds": d("120.000000"),
        "maximum_watch_liquidity_age_seconds": d("600.000000"),
        "maximum_pass_shock_depth_loss_ratio": d("0.100000"),
        "maximum_watch_shock_depth_loss_ratio": d("0.300000"),
        "depth_coverage_weight": d("0.300000"),
        "spread_stability_weight": d("0.200000"),
        "imbalance_volatility_weight": d("0.200000"),
        "liquidity_age_weight": d("0.150000"),
        "shock_sensitivity_weight": d("0.150000"),
        "pass_stability_score": d("0.750000"),
        "watch_stability_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketOrderbookDepthStabilityConfig(**values)


def stability_input(
    bucket_label: str = "depth-stability-pass",
    *,
    sampled_at: datetime | None = None,
    depth_coverage_ratio: Decimal = d("0.900000"),
    spread_instability_ratio: Decimal = d("0.030000"),
    imbalance_volatility_ratio: Decimal = d("0.020000"),
    liquidity_age_seconds: Decimal = d("60.000000"),
    shock_depth_loss_ratio: Decimal = d("0.040000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketOrderbookDepthStabilityInput(
        bucket_label=bucket_label,
        sampled_at=(
            sampled_at
            if sampled_at is not None
            else GENERATED_AT - timedelta(seconds=60)
        ),
        depth_coverage_ratio=depth_coverage_ratio,
        spread_instability_ratio=spread_instability_ratio,
        imbalance_volatility_ratio=imbalance_volatility_ratio,
        liquidity_age_seconds=liquidity_age_seconds,
        shock_depth_loss_ratio=shock_depth_loss_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_orderbook_depth_stability_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_depth_stability_research() -> None:
    module = api()
    empty = report()

    assert module.ORDERBOOK_DEPTH_STABILITY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "ORDERBOOK_DEPTH_STABILITY_STATUSES",
        "DEFAULT_RESEARCH_MARKET_ORDERBOOK_DEPTH_STABILITY_REPORT_CONFIG_VERSION",
        "ResearchMarketOrderbookDepthStabilityConfig",
        "ResearchMarketOrderbookDepthStabilityInput",
        "ResearchMarketOrderbookDepthStabilityReasonCodeCount",
        "ResearchMarketOrderbookDepthStabilityReport",
        "ResearchMarketOrderbookDepthStabilityRow",
        "build_research_market_orderbook_depth_stability_report",
        "research_market_orderbook_depth_stability_report_digest",
        "research_market_orderbook_depth_stability_report_payload",
    )
    assert type(empty) is module.ResearchMarketOrderbookDepthStabilityReport
    assert is_dataclass(empty)
    assert empty.generated_at == GENERATED_AT
    assert empty.config_version == "research-depth-stability-report-v0"
    assert empty.input_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.weak_depth_coverage_count == ZERO
    assert empty.unstable_spread_count == ZERO
    assert empty.high_imbalance_volatility_count == ZERO
    assert empty.aged_liquidity_count == ZERO
    assert empty.shock_sensitive_count == ZERO
    assert empty.average_stability_score is None
    assert empty.min_depth_coverage_ratio == ZERO
    assert empty.max_spread_instability_ratio == ZERO
    assert empty.max_imbalance_volatility_ratio == ZERO
    assert empty.max_liquidity_age_seconds == ZERO
    assert empty.max_shock_depth_loss_ratio == ZERO
    assert empty.status == "block"
    assert empty.rows == ()
    assert empty.reason_codes == ("no_depth_stability_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketOrderbookDepthStabilityReasonCodeCount(
            reason_code="no_depth_stability_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_scores_pass_watch_and_block_depth_stability_inputs() -> None:
    combined = report(
        stability_input(
            "alpha-block",
            depth_coverage_ratio=d("0.200000"),
            spread_instability_ratio=d("0.500000"),
            imbalance_volatility_ratio=d("0.400000"),
            liquidity_age_seconds=d("900.000000"),
            shock_depth_loss_ratio=d("0.500000"),
            reason_codes=("manual_stability_check",),
        ),
        stability_input("beta-pass"),
        stability_input(
            "gamma-watch",
            depth_coverage_ratio=d("0.600000"),
            spread_instability_ratio=d("0.200000"),
            imbalance_volatility_ratio=d("0.150000"),
            liquidity_age_seconds=d("300.000000"),
            shock_depth_loss_ratio=d("0.200000"),
        ),
    )

    assert combined.input_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.weak_depth_coverage_count == d("2.000000")
    assert combined.unstable_spread_count == d("2.000000")
    assert combined.high_imbalance_volatility_count == d("2.000000")
    assert combined.aged_liquidity_count == d("2.000000")
    assert combined.shock_sensitive_count == d("2.000000")
    assert combined.average_stability_score == d("0.500222")
    assert combined.min_depth_coverage_ratio == d("0.200000")
    assert combined.max_spread_instability_ratio == d("0.500000")
    assert combined.max_imbalance_volatility_ratio == d("0.400000")
    assert combined.max_liquidity_age_seconds == d("900.000000")
    assert combined.max_shock_depth_loss_ratio == d("0.500000")
    assert combined.status == "block"
    assert combined.reason_codes == (
        "depth_stability_block",
        "depth_coverage_block",
        "spread_stability_block",
        "imbalance_volatility_block",
        "liquidity_age_block",
        "shock_sensitivity_block",
        "depth_coverage_watch",
        "spread_stability_watch",
        "imbalance_volatility_watch",
        "liquidity_age_watch",
        "shock_sensitivity_watch",
    )

    block_row, pass_row, watch_row = combined.rows
    assert tuple(row.public_row_ref for row in combined.rows) == (
        "depth_stability_group_001",
        "depth_stability_group_002",
        "depth_stability_group_003",
    )
    assert tuple(row.status for row in combined.rows) == ("block", "pass", "watch")
    assert block_row.depth_coverage_score == d("0.250000")
    assert block_row.stability_score == d("0.075000")
    assert block_row.reason_codes == (
        "depth_coverage_block",
        "depth_stability_block",
        "imbalance_volatility_block",
        "input_manual_stability_check",
        "liquidity_age_block",
        "shock_sensitivity_block",
        "spread_stability_block",
    )
    assert pass_row.stability_score == d("0.929000")
    assert pass_row.status == "pass"
    assert "shock_sensitivity_pass" in pass_row.reason_codes
    assert watch_row.stability_score == d("0.496667")
    assert watch_row.status == "watch"
    assert "depth_coverage_watch" in watch_row.reason_codes
    assert "spread_stability_watch" in watch_row.reason_codes
    assert "imbalance_volatility_watch" in watch_row.reason_codes
    assert "liquidity_age_watch" in watch_row.reason_codes
    assert "shock_sensitivity_watch" in watch_row.reason_codes


def test_custom_weights_build_valid_stability_report() -> None:
    weighted = report(
        stability_input(
            depth_coverage_ratio=d("0.700000"),
            spread_instability_ratio=d("0.120000"),
            imbalance_volatility_ratio=d("0.080000"),
            liquidity_age_seconds=d("100.000000"),
            shock_depth_loss_ratio=d("0.080000"),
        ),
        cfg=config(
            depth_coverage_weight=d("0.100000"),
            spread_stability_weight=d("0.300000"),
            imbalance_volatility_weight=d("0.250000"),
            liquidity_age_weight=d("0.200000"),
            shock_sensitivity_weight=d("0.150000"),
        ),
    )

    assert weighted.input_count == d("1.000000")
    assert weighted.rows[0].stability_score == d("0.714167")
    assert weighted.average_stability_score == d("0.714167")
    assert weighted.rows[0].status == "watch"
    assert weighted.status == "watch"


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        stability_input("zulu-depth-stability", reason_codes=("zeta", "alpha")),
        stability_input("alpha-depth-stability"),
    )
    second = report(
        stability_input("alpha-depth-stability"),
        stability_input("zulu-depth-stability", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_orderbook_depth_stability_report_payload(first)
    second_payload = module.research_market_orderbook_depth_stability_report_payload(second)
    digest_payload = dict(first_payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    public_encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_market_orderbook_depth_stability_report_digest(first) == digest
    assert first.derived_validation_digest == digest
    assert first_payload["derived_validation_digest"] == digest
    assert first_payload["rows"][0]["public_row_ref"] == "depth_stability_group_001"
    assert first_payload["rows"][0]["depth_coverage_ratio"] == "0.900000"
    assert first_payload["rows"][0]["stability_score"] == "0.929000"
    assert "alpha-depth-stability" not in public_encoded
    assert "zulu-depth-stability" not in public_encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in public_encoded
    assert not any(
        _has_forbidden_public_surface(value)
        for value in _walk_payload_keys(first_payload) + _walk_payload_strings(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(stability_input())

    for value in (config(), stability_input(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_age_seconds",
                    "_count",
                    "_ratio",
                    "_score",
                    "_weight",
                    "_seconds",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].stability_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="minimum_pass_depth_coverage_ratio"):
        config(minimum_pass_depth_coverage_ratio=DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="maximum_watch_spread_instability_ratio"):
        config(maximum_watch_spread_instability_ratio=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights"):
        config(shock_sensitivity_weight=d("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(stability_input(), generated_at=datetime(2026, 7, 8, 21, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            stability_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 21, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="sampled_at"):
        report(stability_input(sampled_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="bucket_label"):
        stability_input(" market-id")
    with pytest.raises(ValueError, match="bucket_label"):
        stability_input("market_id_alpha")
    with pytest.raises(ValueError, match="bucket_label"):
        stability_input("question_alpha")
    with pytest.raises(ValueError, match="depth_coverage_ratio"):
        stability_input(depth_coverage_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="sampled_at"):
        stability_input(sampled_at=datetime(2026, 7, 8, 21, 0))
    with pytest.raises(ValueError, match="spread_instability_ratio"):
        stability_input(spread_instability_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="imbalance_volatility_ratio"):
        stability_input(imbalance_volatility_ratio=-d("0.100000"))
    with pytest.raises(ValueError, match="liquidity_age_seconds"):
        stability_input(liquidity_age_seconds=DecimalSubclass("60.000000"))
    with pytest.raises(ValueError, match="shock_depth_loss_ratio"):
        stability_input(shock_depth_loss_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        stability_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="reason_codes"):
        stability_input(reason_codes=("source_url_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(stability_input(), paper_only=False)
    with pytest.raises(ValueError, match="stability_score"):
        replace(populated.rows[0], stability_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_orderbook_depth_stability_report_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


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


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _walk_payload_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, str):
        strings.append(value)
    return tuple(strings)


def _has_forbidden_public_surface(value: str) -> bool:
    lowered = value.lower()
    return any(
        term in lowered
        for term in (
            "candidate_id",
            "condition_id",
            "market_id",
            "market_slug",
            "question",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
            "live",
        )
    )
