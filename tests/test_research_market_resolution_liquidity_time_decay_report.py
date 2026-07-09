from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_resolution_liquidity_time_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_TIME_DECAY_REPORT_CONFIG_VERSION
        ),
        "max_pass_book_age_seconds": d("300.000000"),
        "max_watch_book_age_seconds": d("1200.000000"),
        "min_pass_resolution_window_seconds": d("3600.000000"),
        "min_watch_resolution_window_seconds": d("900.000000"),
        "min_pass_depth_retention_ratio": d("0.850000"),
        "min_watch_depth_retention_ratio": d("0.500000"),
        "max_pass_depth_decay_ratio": d("0.150000"),
        "max_watch_depth_decay_ratio": d("0.500000"),
        "max_pass_spread_widening_ratio": d("0.020000"),
        "max_watch_spread_widening_ratio": d("0.120000"),
        "max_pass_time_decay_pressure": d("0.200000"),
        "max_watch_time_decay_pressure": d("0.600000"),
        "min_pass_liquidity_half_life_seconds": d("7200.000000"),
        "min_watch_liquidity_half_life_seconds": d("1800.000000"),
        "pass_decay_score": d("0.750000"),
        "watch_decay_score": d("0.450000"),
        "depth_retention_weight": d("0.250000"),
        "depth_decay_weight": d("0.200000"),
        "spread_widening_weight": d("0.150000"),
        "book_age_weight": d("0.100000"),
        "resolution_window_weight": d("0.100000"),
        "time_decay_pressure_weight": d("0.100000"),
        "liquidity_half_life_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchMarketResolutionLiquidityTimeDecayConfig(**values)


def snapshot(
    liquidity_snapshot_key: str = "liquidity-decay-pass",
    *,
    observed_at: datetime | None = None,
    resolution_window_seconds: Decimal = d("7200.000000"),
    baseline_depth: Decimal = d("1000.000000"),
    current_depth: Decimal = d("900.000000"),
    baseline_spread_ratio: Decimal = d("0.020000"),
    current_spread_ratio: Decimal = d("0.030000"),
    liquidity_half_life_seconds: Decimal = d("9000.000000"),
    time_decay_pressure: Decimal = d("0.150000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketResolutionLiquidityTimeDecaySnapshot(
        liquidity_snapshot_key=liquidity_snapshot_key,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=120),
        resolution_window_seconds=resolution_window_seconds,
        baseline_depth=baseline_depth,
        current_depth=current_depth,
        baseline_spread_ratio=baseline_spread_ratio,
        current_spread_ratio=current_spread_ratio,
        liquidity_half_life_seconds=liquidity_half_life_seconds,
        time_decay_pressure=time_decay_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_resolution_liquidity_time_decay_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_resolution_liquidity_time_decay_review() -> None:
    module = api()
    decay_report = report()

    assert module.RESOLUTION_LIQUIDITY_TIME_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "RESOLUTION_LIQUIDITY_TIME_DECAY_STATUSES",
        "DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_TIME_DECAY_REPORT_CONFIG_VERSION",
        "ResearchMarketResolutionLiquidityTimeDecayConfig",
        "ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount",
        "ResearchMarketResolutionLiquidityTimeDecayReport",
        "ResearchMarketResolutionLiquidityTimeDecayRow",
        "ResearchMarketResolutionLiquidityTimeDecaySnapshot",
        "build_research_market_resolution_liquidity_time_decay_report",
        "research_market_resolution_liquidity_time_decay_report_digest",
        "research_market_resolution_liquidity_time_decay_report_payload",
    )
    assert type(decay_report) is module.ResearchMarketResolutionLiquidityTimeDecayReport
    assert is_dataclass(decay_report)
    assert decay_report.generated_at == GENERATED_AT
    assert decay_report.config_version == (
        "research-market-resolution-liquidity-time-decay-report-v0"
    )
    assert decay_report.input_count == ZERO
    assert decay_report.pass_count == ZERO
    assert decay_report.watch_count == ZERO
    assert decay_report.block_count == ZERO
    assert decay_report.average_decay_score is None
    assert decay_report.min_depth_retention_ratio == ZERO
    assert decay_report.max_depth_decay_ratio == ZERO
    assert decay_report.max_spread_widening_ratio == ZERO
    assert decay_report.max_book_age_seconds == ZERO
    assert decay_report.min_resolution_window_seconds == ZERO
    assert decay_report.max_time_decay_pressure == ZERO
    assert decay_report.min_liquidity_half_life_seconds == ZERO
    assert decay_report.status == "block"
    assert decay_report.reason_codes == (
        "no_resolution_liquidity_time_decay_snapshots",
    )
    assert decay_report.reason_code_counts == (
        module.ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount(
            reason_code="no_resolution_liquidity_time_decay_snapshots",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert decay_report.rows == ()
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True


def test_scores_pass_watch_and_block_liquidity_time_decay() -> None:
    decay_report = report(
        snapshot(
            "liquidity-decay-watch",
            observed_at=GENERATED_AT - timedelta(seconds=600),
            resolution_window_seconds=d("1800.000000"),
            baseline_depth=d("1000.000000"),
            current_depth=d("650.000000"),
            baseline_spread_ratio=d("0.020000"),
            current_spread_ratio=d("0.080000"),
            liquidity_half_life_seconds=d("3600.000000"),
            time_decay_pressure=d("0.350000"),
        ),
        snapshot(
            "liquidity-decay-block",
            observed_at=GENERATED_AT - timedelta(seconds=1800),
            resolution_window_seconds=d("600.000000"),
            baseline_depth=d("1000.000000"),
            current_depth=d("350.000000"),
            baseline_spread_ratio=d("0.020000"),
            current_spread_ratio=d("0.170000"),
            liquidity_half_life_seconds=d("1200.000000"),
            time_decay_pressure=d("0.750000"),
            reason_codes=("manual_review",),
        ),
        snapshot("liquidity-decay-pass"),
    )

    assert decay_report.input_count == d("3.000000")
    assert decay_report.pass_count == d("1.000000")
    assert decay_report.watch_count == d("1.000000")
    assert decay_report.block_count == d("1.000000")
    assert decay_report.average_decay_score == d("0.522206")
    assert decay_report.min_depth_retention_ratio == d("0.350000")
    assert decay_report.max_depth_decay_ratio == d("0.650000")
    assert decay_report.max_spread_widening_ratio == d("0.150000")
    assert decay_report.max_book_age_seconds == d("1800.000000")
    assert decay_report.min_resolution_window_seconds == d("600.000000")
    assert decay_report.max_time_decay_pressure == d("0.750000")
    assert decay_report.min_liquidity_half_life_seconds == d("1200.000000")
    assert decay_report.status == "block"

    block_row, pass_row, watch_row = decay_report.rows
    assert tuple(row.public_decay_ref for row in decay_report.rows) == (
        "resolution_liquidity_decay_group_001",
        "resolution_liquidity_decay_group_002",
        "resolution_liquidity_decay_group_003",
    )
    assert tuple(row.status for row in decay_report.rows) == (
        "block",
        "pass",
        "watch",
    )
    assert block_row.depth_retention_ratio == d("0.350000")
    assert block_row.depth_decay_ratio == d("0.650000")
    assert block_row.spread_widening_ratio == d("0.150000")
    assert block_row.book_age_score == ZERO
    assert block_row.decay_score == d("0.136275")
    assert block_row.reason_codes == (
        "book_age_block",
        "decay_score_block",
        "depth_decay_block",
        "depth_retention_block",
        "input_manual_review",
        "liquidity_half_life_block",
        "resolution_window_block",
        "spread_widening_block",
        "time_decay_pressure_block",
    )
    assert pass_row.depth_retention_score == d("1.000000")
    assert pass_row.depth_decay_score == d("0.800000")
    assert pass_row.spread_widening_score == d("0.916667")
    assert pass_row.book_age_score == d("0.900000")
    assert pass_row.resolution_window_score == d("1.000000")
    assert pass_row.time_decay_pressure_score == d("0.750000")
    assert pass_row.liquidity_half_life_score == d("1.000000")
    assert pass_row.decay_score == d("0.912500")
    assert pass_row.reason_codes == (
        "book_age_pass",
        "decay_score_pass",
        "depth_decay_pass",
        "depth_retention_pass",
        "liquidity_half_life_pass",
        "resolution_window_pass",
        "spread_widening_pass",
        "time_decay_pressure_pass",
    )
    assert watch_row.depth_retention_score == d("0.764706")
    assert watch_row.depth_decay_score == d("0.300000")
    assert watch_row.spread_widening_score == d("0.500000")
    assert watch_row.decay_score == d("0.517843")
    assert watch_row.reason_codes == (
        "book_age_watch",
        "decay_score_watch",
        "depth_decay_watch",
        "depth_retention_watch",
        "liquidity_half_life_watch",
        "resolution_window_watch",
        "spread_widening_watch",
        "time_decay_pressure_watch",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        snapshot("liquidity-decay-z", reason_codes=("zeta", "alpha")),
        snapshot("liquidity-decay-a"),
    )
    second = report(
        snapshot("liquidity-decay-a"),
        snapshot("liquidity-decay-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_resolution_liquidity_time_decay_report_payload(
        first,
    )
    second_payload = module.research_market_resolution_liquidity_time_decay_report_payload(
        second,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert (
        module.research_market_resolution_liquidity_time_decay_report_digest(first)
        == module.research_market_resolution_liquidity_time_decay_report_digest(second)
        == first.derived_validation_digest
    )
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["public_decay_ref"] == (
        "resolution_liquidity_decay_group_001"
    )
    assert first_payload["rows"][0]["decay_score"] == "0.912500"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "liquidity-decay-a" not in encoded
    assert "liquidity-decay-z" not in encoded
    assert not any(
        _has_forbidden_public_surface(str(value))
        for value in _walk_payload_strings(first_payload)
    )
    assert not any(
        _has_forbidden_public_surface(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_payload_and_digest_do_not_depend_on_private_snapshot_keys() -> None:
    module = api()
    first = report(
        snapshot(
            "liquidity-decay-b",
            current_depth=d("650.000000"),
            current_spread_ratio=d("0.080000"),
            resolution_window_seconds=d("1800.000000"),
            liquidity_half_life_seconds=d("3600.000000"),
            time_decay_pressure=d("0.350000"),
        ),
        snapshot("liquidity-decay-a"),
    )
    second = report(
        snapshot(
            "liquidity-decay-y",
            current_depth=d("650.000000"),
            current_spread_ratio=d("0.080000"),
            resolution_window_seconds=d("1800.000000"),
            liquidity_half_life_seconds=d("3600.000000"),
            time_decay_pressure=d("0.350000"),
        ),
        snapshot("liquidity-decay-z"),
    )

    first_payload = module.research_market_resolution_liquidity_time_decay_report_payload(
        first,
    )
    second_payload = module.research_market_resolution_liquidity_time_decay_report_payload(
        second,
    )

    assert first_payload == second_payload
    assert module.research_market_resolution_liquidity_time_decay_report_digest(
        first,
    ) == module.research_market_resolution_liquidity_time_decay_report_digest(second)


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(snapshot())

    for value in (
        config(),
        snapshot(),
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].decay_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="baseline_depth"):
        snapshot(baseline_depth=1000)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="current_depth"):
        snapshot(current_depth=DecimalSubclass("900.000000"))
    with pytest.raises(ValueError, match="time_decay_pressure"):
        snapshot(time_decay_pressure=d("1.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(snapshot(), generated_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="current_depth"):
        snapshot(baseline_depth=d("100.000000"), current_depth=d("101.000000"))
    with pytest.raises(ValueError, match="current_spread_ratio"):
        snapshot(baseline_spread_ratio=d("0.040000"), current_spread_ratio=d("0.030000"))
    with pytest.raises(ValueError, match="reason_codes"):
        snapshot(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="unsafe public"):
        snapshot(reason_codes=("market_id",))
    with pytest.raises(ValueError, match="paper_only"):
        snapshot(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchMarketResolutionLiquidityTimeDecayConfig,), {})


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
            keys.append(str(key))
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
    normalized = value.lower()
    forbidden_fragments = (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "position",
        "sizing",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)
