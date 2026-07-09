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
    "research_market_probability_cost_dislocation_monitor_report"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
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
            module.DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_DISLOCATION_MONITOR_CONFIG_VERSION
        ),
        "watch_probability_gap_ratio": d("0.050000"),
        "block_probability_gap_ratio": d("0.120000"),
        "watch_cost_pressure_ratio": d("0.030000"),
        "block_cost_pressure_ratio": d("0.080000"),
        "watch_net_dislocation_ratio": d("0.020000"),
        "block_net_dislocation_ratio": d("0.070000"),
        "watch_dislocation_score": d("0.300000"),
        "block_dislocation_score": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityCostDislocationMonitorConfig(**values)


def signal(
    public_signal_ref: str = "public-signal-alpha",
    *,
    observed_at: datetime | None = None,
    estimated_probability: Decimal = d("0.520000"),
    displayed_probability: Decimal = d("0.500000"),
    fee_ratio: Decimal = d("0.004000"),
    spread_ratio: Decimal = d("0.006000"),
    slippage_ratio: Decimal = d("0.004000"),
    confidence_ratio: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketProbabilityCostDislocationMonitorInput(
        public_signal_ref=public_signal_ref,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=5),
        estimated_probability=estimated_probability,
        displayed_probability=displayed_probability,
        fee_ratio=fee_ratio,
        spread_ratio=spread_ratio,
        slippage_ratio=slippage_ratio,
        confidence_ratio=confidence_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *signals: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_probability_cost_dislocation_monitor_report(
        signals,
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


def test_dislocation_monitor_classifies_block_watch_pass_rows() -> None:
    module = api()
    built = report(
        signal("quiet-public-signal"),
        signal(
            "watch-public-signal",
            estimated_probability=d("0.570000"),
            displayed_probability=d("0.500000"),
            fee_ratio=d("0.010000"),
            spread_ratio=d("0.012000"),
            slippage_ratio=d("0.010000"),
            confidence_ratio=d("0.800000"),
        ),
        signal(
            "blocked-public-signal",
            estimated_probability=d("0.700000"),
            displayed_probability=d("0.500000"),
            fee_ratio=d("0.020000"),
            spread_ratio=d("0.040000"),
            slippage_ratio=d("0.030000"),
            confidence_ratio=d("0.600000"),
            reason_codes=("public_cost_marker",),
        ),
    )

    assert type(built) is module.ResearchMarketProbabilityCostDislocationMonitorReport
    assert is_dataclass(built)
    assert module.STATUSES == ("pass", "watch", "block")
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.block_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.pass_count == d("1.000000")
    assert built.probability_gap_watch_count == d("2.000000")
    assert built.cost_pressure_watch_count == d("2.000000")
    assert built.net_dislocation_watch_count == d("2.000000")
    assert built.max_probability_gap_ratio == d("0.200000")
    assert built.max_cost_pressure_ratio == d("0.090000")
    assert built.max_net_dislocation_ratio == d("0.110000")
    assert built.average_dislocation_score == d("0.542857")

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.public_signal_ref == "blocked-public-signal"
    assert blocked.probability_gap_ratio == d("0.200000")
    assert blocked.cost_pressure_ratio == d("0.090000")
    assert blocked.net_dislocation_ratio == d("0.110000")
    assert blocked.dislocation_score == d("1.000000")
    assert blocked.reason_codes == (
        "input_public_cost_marker",
        "probability_cost_dislocation_monitor_cost_pressure_block",
        "probability_cost_dislocation_monitor_dislocation_score_block",
        "probability_cost_dislocation_monitor_net_dislocation_block",
        "probability_cost_dislocation_monitor_probability_gap_block",
    )
    assert watched.net_dislocation_ratio == d("0.038000")
    assert watched.dislocation_score == d("0.542857")
    assert watched.reason_codes == (
        "probability_cost_dislocation_monitor_cost_pressure_watch",
        "probability_cost_dislocation_monitor_dislocation_score_watch",
        "probability_cost_dislocation_monitor_net_dislocation_watch",
        "probability_cost_dislocation_monitor_probability_gap_watch",
    )
    assert passed.net_dislocation_ratio == d("0.006000")
    assert passed.dislocation_score == d("0.085714")
    assert passed.reason_codes == ("probability_cost_dislocation_monitor_clear",)
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_net_dislocation_floors_probability_gap_after_cost_pressure() -> None:
    built = report(
        signal(
            "cost-covered-public-signal",
            estimated_probability=d("0.560000"),
            displayed_probability=d("0.500000"),
            fee_ratio=d("0.020000"),
            spread_ratio=d("0.020000"),
            slippage_ratio=d("0.020000"),
        ),
        signal(
            "net-block-public-signal",
            estimated_probability=d("0.620000"),
            displayed_probability=d("0.500000"),
            fee_ratio=d("0.005000"),
            spread_ratio=d("0.010000"),
            slippage_ratio=d("0.005000"),
        ),
    )

    blocked, covered = built.rows
    assert blocked.public_signal_ref == "net-block-public-signal"
    assert blocked.probability_gap_ratio == d("0.120000")
    assert blocked.cost_pressure_ratio == d("0.020000")
    assert blocked.net_dislocation_ratio == d("0.100000")
    assert blocked.status == "block"
    assert "probability_cost_dislocation_monitor_net_dislocation_block" in blocked.reason_codes

    assert covered.public_signal_ref == "cost-covered-public-signal"
    assert covered.net_dislocation_ratio == ZERO
    assert covered.status == "watch"
    assert "probability_cost_dislocation_monitor_net_dislocation_watch" not in covered.reason_codes


def test_public_payload_and_digest_are_deterministic_decimal_stringed_and_safe() -> None:
    module = api()
    first = report(
        signal("beta-public-signal", estimated_probability=d("0.570000")),
        signal("alpha-public-signal"),
    )
    second = report(
        signal("alpha-public-signal"),
        signal("beta-public-signal", estimated_probability=d("0.570000")),
    )

    first_payload = module.research_market_probability_cost_dislocation_monitor_public_payload(
        first,
    )
    second_payload = module.research_market_probability_cost_dislocation_monitor_public_payload(
        second,
    )
    digest = module.research_market_probability_cost_dislocation_monitor_digest(first)

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
    assert digest == module.research_market_probability_cost_dislocation_monitor_digest(second)
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["input_count"] == "2.000000"
    assert first_payload["rows"][0]["public_signal_ref"] == "beta-public-signal"
    assert first_payload["rows"][0]["estimated_probability"] == "0.570000"
    assert first_payload["reason_code_counts"][0]["count"] == "1.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))

    encoded = json.dumps(first_payload)
    forbidden = (
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
    )
    assert all(term not in encoded for term in forbidden)


def test_payload_revalidates_tampering_and_public_safety() -> None:
    module = api()
    built = report(signal())

    object.__setattr__(built, "input_count", d("2.000000"))
    with pytest.raises(ValueError, match="input_count"):
        module.research_market_probability_cost_dislocation_monitor_public_payload(built)
    object.__setattr__(built, "input_count", d("1.000000"))

    object.__setattr__(built, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_probability_cost_dislocation_monitor_public_payload(built)

    good = report(signal())
    unsafe_row = good.rows[0]
    object.__setattr__(unsafe_row, "public_signal_ref", "market-slug-ra" + "w")
    object.__setattr__(good, "rows", (unsafe_row,))
    with pytest.raises(ValueError, match="unsafe|public_signal_ref"):
        module.research_market_probability_cost_dislocation_monitor_public_payload(good)

    with pytest.raises(ValueError, match="public_signal_ref"):
        signal(public_signal_ref="market-id-ra" + "w")
    with pytest.raises(ValueError, match="public_signal_ref"):
        signal(public_signal_ref="will-fed-cut-rates-in-july")
    with pytest.raises(ValueError, match="public_signal_ref"):
        signal(public_signal_ref="123e4567-e89b-12d3-a456-426614174000")
    with pytest.raises(ValueError, match="reason_codes"):
        signal(reason_codes=("NeedsReview",))
    with pytest.raises(ValueError, match="reason_codes"):
        signal(reason_codes=("will_trump_win",))
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report"):
        module.research_market_probability_cost_dislocation_monitor_public_payload(
            {"payload": 1},
        )
    with pytest.raises(ValueError, match="report"):
        module.research_market_probability_cost_dislocation_monitor_digest({"payload": 1})


def test_custom_config_validation_and_decimal_only_exact_types() -> None:
    module = api()
    custom = config(
        watch_probability_gap_ratio=d("0.070000"),
        block_probability_gap_ratio=d("0.140000"),
        watch_cost_pressure_ratio=d("0.060000"),
        block_cost_pressure_ratio=d("0.120000"),
        watch_dislocation_score=d("0.500000"),
        block_dislocation_score=d("0.900000"),
    )
    built = report(
        signal(
            estimated_probability=d("0.560000"),
            displayed_probability=d("0.500000"),
            fee_ratio=d("0.010000"),
            spread_ratio=d("0.020000"),
            slippage_ratio=d("0.020000"),
        ),
        cfg=custom,
    )

    assert built.status == "pass"
    assert built.rows[0].cost_pressure_ratio == d("0.050000")
    assert built.rows[0].net_dislocation_ratio == d("0.010000")
    assert built.rows[0].dislocation_score == d("0.142857")
    assert built.rows[0].status == "pass"

    for public_type in (
        module.ResearchMarketProbabilityCostDislocationMonitorConfig,
        module.ResearchMarketProbabilityCostDislocationMonitorInput,
        module.ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount,
        module.ResearchMarketProbabilityCostDislocationMonitorReport,
        module.ResearchMarketProbabilityCostDislocationMonitorRow,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen
        assert all("float" not in str(field.type) for field in fields(public_type))
        assert all("int" not in str(field.type) for field in fields(public_type))

    with pytest.raises(FrozenInstanceError):
        built.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].dislocation_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="watch_cost_pressure_ratio"):
        config(watch_cost_pressure_ratio=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="watch_cost_pressure_ratio"):
        config(watch_cost_pressure_ratio=0.03)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_cost_pressure_ratio"):
        config(watch_cost_pressure_ratio=d("0.090000"))
    with pytest.raises(ValueError, match="block_net_dislocation_ratio"):
        config(block_net_dislocation_ratio=d("0.010000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="unsupported-config")
    with pytest.raises(ValueError, match="fee_ratio"):
        signal(fee_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="estimated_probability"):
        signal(estimated_probability=d("1.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(signal(), generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_owned_module_has_no_io_db_or_private_action_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_probability_cost_dislocation_monitor_report.py"
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
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
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
