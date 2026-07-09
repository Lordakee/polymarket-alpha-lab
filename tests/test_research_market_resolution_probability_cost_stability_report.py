from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_resolution_probability_cost_stability_report"
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_RESOLUTION_PROBABILITY_COST_STABILITY_CONFIG_VERSION
        ),
        "watch_resolution_time_shift_seconds": d("3600.000000"),
        "block_resolution_time_shift_seconds": d("7200.000000"),
        "watch_market_probability_range": d("0.050000"),
        "block_market_probability_range": d("0.120000"),
        "watch_cost_pressure_ratio": d("0.040000"),
        "block_cost_pressure_ratio": d("0.100000"),
        "watch_depth_resilience_ratio": d("0.600000"),
        "block_depth_resilience_ratio": d("0.300000"),
        "watch_stability_score": d("0.700000"),
        "block_stability_score": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchMarketResolutionProbabilityCostStabilityConfig(**values)


def input_row(
    public_event_ref: str = "public-event-alpha",
    *,
    observed_at: datetime | None = None,
    resolution_time_shift_seconds: Decimal = d("600.000000"),
    market_probability_min: Decimal = d("0.490000"),
    market_probability_max: Decimal = d("0.510000"),
    fee_ratio: Decimal = d("0.005000"),
    spread_ratio: Decimal = d("0.010000"),
    slippage_ratio: Decimal = d("0.005000"),
    depth_resilience_ratio: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketResolutionProbabilityCostStabilityInput(
        public_event_ref=public_event_ref,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=10),
        resolution_time_shift_seconds=resolution_time_shift_seconds,
        market_probability_min=market_probability_min,
        market_probability_max=market_probability_max,
        fee_ratio=fee_ratio,
        spread_ratio=spread_ratio,
        slippage_ratio=slippage_ratio,
        depth_resilience_ratio=depth_resilience_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *inputs: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_resolution_probability_cost_stability_report(
        inputs,
        config=cfg or config(),
        generated_at=generated_at,
    )


def payload_without_digest(payload: dict[str, object]) -> dict[str, object]:
    trimmed = dict(payload)
    trimmed.pop("derived_validation_digest", None)
    return trimmed


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_payload_values(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def test_stability_scoring_classifies_block_watch_pass_rows() -> None:
    module = api()
    built = report(
        input_row("quiet-public-event"),
        input_row(
            "watch-public-event",
            resolution_time_shift_seconds=d("4000.000000"),
            market_probability_min=d("0.440000"),
            market_probability_max=d("0.500000"),
            fee_ratio=d("0.010000"),
            spread_ratio=d("0.020000"),
            slippage_ratio=d("0.020000"),
            depth_resilience_ratio=d("0.500000"),
        ),
        input_row(
            "blocked-public-event",
            resolution_time_shift_seconds=d("8000.000000"),
            market_probability_min=d("0.200000"),
            market_probability_max=d("0.350000"),
            fee_ratio=d("0.040000"),
            spread_ratio=d("0.050000"),
            slippage_ratio=d("0.030000"),
            depth_resilience_ratio=d("0.200000"),
            reason_codes=("public_depth_marker",),
        ),
    )

    assert type(built) is module.ResearchMarketResolutionProbabilityCostStabilityReport
    assert is_dataclass(built)
    assert module.STATUSES == ("pass", "watch", "block")
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.block_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.pass_count == d("1.000000")
    assert built.resolution_timing_watch_count == d("2.000000")
    assert built.market_probability_watch_count == d("2.000000")
    assert built.cost_pressure_watch_count == d("2.000000")
    assert built.depth_resilience_watch_count == d("2.000000")
    assert built.min_stability_score == ZERO
    assert built.average_stability_score == d("0.414815")

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.public_event_ref == "blocked-public-event"
    assert blocked.market_probability_range == d("0.150000")
    assert blocked.cost_pressure_ratio == d("0.120000")
    assert blocked.stability_score == ZERO
    assert blocked.reason_codes == (
        "input_public_depth_marker",
        "resolution_probability_cost_stability_cost_pressure_block",
        "resolution_probability_cost_stability_depth_resilience_block",
        "resolution_probability_cost_stability_probability_stability_block",
        "resolution_probability_cost_stability_resolution_timing_block",
        "resolution_probability_cost_stability_stability_score_block",
    )
    assert watched.stability_score == d("0.444444")
    assert watched.reason_codes == (
        "resolution_probability_cost_stability_cost_pressure_watch",
        "resolution_probability_cost_stability_depth_resilience_watch",
        "resolution_probability_cost_stability_probability_stability_watch",
        "resolution_probability_cost_stability_resolution_timing_watch",
        "resolution_probability_cost_stability_stability_score_watch",
    )
    assert passed.stability_score == d("0.800000")
    assert passed.reason_codes == (
        "resolution_probability_cost_stability_clear",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_cost_pressure_thresholds_sum_fee_spread_and_slippage() -> None:
    built = report(
        input_row(
            "cost-watch-public-event",
            fee_ratio=d("0.010000"),
            spread_ratio=d("0.020000"),
            slippage_ratio=d("0.010000"),
        ),
        input_row(
            "cost-block-public-event",
            fee_ratio=d("0.040000"),
            spread_ratio=d("0.040000"),
            slippage_ratio=d("0.020000"),
        ),
    )

    blocked, watched = built.rows
    assert blocked.public_event_ref == "cost-block-public-event"
    assert blocked.cost_pressure_ratio == d("0.100000")
    assert blocked.cost_pressure_score == ZERO
    assert blocked.status == "block"
    assert "resolution_probability_cost_stability_cost_pressure_block" in blocked.reason_codes

    assert watched.public_event_ref == "cost-watch-public-event"
    assert watched.cost_pressure_ratio == d("0.040000")
    assert watched.cost_pressure_score == d("0.600000")
    assert watched.status == "watch"
    assert "resolution_probability_cost_stability_cost_pressure_watch" in watched.reason_codes


def test_public_payload_and_digest_are_deterministic_decimal_stringed_and_safe() -> None:
    module = api()
    first = report(
        input_row("beta-public-event", resolution_time_shift_seconds=d("4000.000000")),
        input_row("alpha-public-event"),
    )
    second = report(
        input_row("alpha-public-event"),
        input_row("beta-public-event", resolution_time_shift_seconds=d("4000.000000")),
    )

    first_payload = module.research_market_resolution_probability_cost_stability_public_payload(
        first,
    )
    second_payload = (
        module.research_market_resolution_probability_cost_stability_public_payload(second)
    )
    digest = module.research_market_resolution_probability_cost_stability_digest(first)

    assert first == second
    assert first.public_payload == first_payload
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True)
    assert digest == hashlib.sha256(
        json.dumps(
            payload_without_digest(first_payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert digest == first_payload["derived_validation_digest"]
    assert digest == module.research_market_resolution_probability_cost_stability_digest(
        second,
    )
    assert first_payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert first_payload["input_count"] == "2.000000"
    assert first_payload["rows"][0]["public_event_ref"] == "beta-public-event"
    assert first_payload["rows"][0]["resolution_time_shift_seconds"] == "4000.000000"
    assert first_payload["rows"][0]["stability_score"] == "0.444444"
    assert first_payload["reason_code_counts"][0]["count"] == "1.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))

    encoded = json.dumps(first_payload)
    for unsafe in (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "sizing",
        "recommend",
        "://",
        "?",
    ):
        assert unsafe not in encoded


def test_payload_revalidates_tampering_and_public_safety() -> None:
    module = api()
    built = report(input_row())

    object.__setattr__(built, "input_count", d("2.000000"))
    with pytest.raises(ValueError, match="input_count"):
        module.research_market_resolution_probability_cost_stability_public_payload(built)
    object.__setattr__(built, "input_count", d("1.000000"))

    object.__setattr__(built, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_resolution_probability_cost_stability_public_payload(built)

    good = report(input_row())
    unsafe_row = good.rows[0]
    object.__setattr__(unsafe_row, "public_event_ref", "market-slug-ra" + "w")
    object.__setattr__(good, "rows", (unsafe_row,))
    with pytest.raises(ValueError, match="unsafe|public_event_ref"):
        module.research_market_resolution_probability_cost_stability_public_payload(good)

    with pytest.raises(ValueError, match="public_event_ref"):
        input_row(public_event_ref="market-id-ra" + "w")
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("NeedsReview",))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report"):
        module.research_market_resolution_probability_cost_stability_public_payload(
            {"payload": 1},
        )
    with pytest.raises(ValueError, match="report"):
        module.research_market_resolution_probability_cost_stability_digest({"payload": 1})


def test_custom_config_validation_and_decimal_only_exact_types() -> None:
    module = api()
    custom = config(
        watch_cost_pressure_ratio=d("0.060000"),
        block_cost_pressure_ratio=d("0.140000"),
        watch_stability_score=d("0.500000"),
        block_stability_score=d("0.250000"),
    )
    built = report(
        input_row(
            fee_ratio=d("0.010000"),
            spread_ratio=d("0.020000"),
            slippage_ratio=d("0.020000"),
        ),
        cfg=custom,
    )

    assert built.status == "pass"
    assert built.rows[0].cost_pressure_ratio == d("0.050000")
    assert built.rows[0].cost_pressure_score == d("0.642857")
    assert built.rows[0].status == "pass"

    for public_type in (
        module.ResearchMarketResolutionProbabilityCostStabilityConfig,
        module.ResearchMarketResolutionProbabilityCostStabilityInput,
        module.ResearchMarketResolutionProbabilityCostStabilityReasonCodeCount,
        module.ResearchMarketResolutionProbabilityCostStabilityReport,
        module.ResearchMarketResolutionProbabilityCostStabilityRow,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen
        assert all("float" not in str(field.type) for field in fields(public_type))
        assert all("int" not in str(field.type) for field in fields(public_type))

    with pytest.raises(FrozenInstanceError):
        built.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].stability_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="watch_cost_pressure_ratio"):
        config(watch_cost_pressure_ratio=_DecimalSubclass("0.040000"))
    with pytest.raises(ValueError, match="watch_cost_pressure_ratio"):
        config(watch_cost_pressure_ratio=0.04)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_cost_pressure_ratio"):
        config(watch_cost_pressure_ratio=d("0.120000"))
    with pytest.raises(ValueError, match="block_depth_resilience_ratio"):
        config(block_depth_resilience_ratio=d("0.700000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="unsupported-config")
    with pytest.raises(ValueError, match="fee_ratio"):
        input_row(fee_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_time_shift_seconds"):
        input_row(resolution_time_shift_seconds=600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_probability_min"):
        input_row(market_probability_min=d("0.600000"), market_probability_max=d("0.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_owned_module_has_no_io_db_or_private_action_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_resolution_probability_cost_stability_report.py"
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
        "psycopg",
        "sqlite",
        "supabase",
        "private_key",
        "api_key",
        "secret",
        "credential",
        "buy",
        "sell",
        "position",
        "recommend",
        "sizing",
        "submit",
        "cancel",
        "live",
        "wallet",
        "order",
        "trade",
    )

    assert all(term not in source for term in forbidden_terms)
