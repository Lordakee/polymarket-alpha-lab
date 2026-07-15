from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_discovery_candidate_pool"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_discovery_candidate_pool.py"
)
GENERATED_AT = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


class StringSubclass(str):
    pass


class TupleSubclass(tuple):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing market discovery candidate pool module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def test_public_dataclasses_cannot_be_subclassed() -> None:
    module = api()
    for base in (
        module.MarketDiscoveryCandidatePoolConfig,
        module.MarketDiscoveryCandidate,
        module.MarketDiscoveryCandidatePoolRow,
        module.MarketDiscoveryCandidatePoolReasonCodeCount,
        module.MarketDiscoveryCandidatePoolReadinessReport,
    ):
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"Unsafe{base.__name__}", (base,), {"__post_init__": lambda self: None})


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": module.DEFAULT_MARKET_DISCOVERY_CANDIDATE_POOL_CONFIG_VERSION,
        "min_liquidity": d("1000.000000"),
        "max_spread": d("0.050000"),
        "max_data_age_seconds": d("300.000000"),
        "min_seconds_until_end": d("3600.000000"),
    }
    values.update(overrides)
    return module.MarketDiscoveryCandidatePoolConfig(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "market_id": "market-alpha-001",
        "slug": "will-alpha-happen",
        "question": "Will alpha happen by Friday?",
        "category": "politics",
        "liquidity": d("2500.000000"),
        "spread": d("0.020000"),
        "end_time": GENERATED_AT + timedelta(days=7),
        "data_freshness": d("30.000000"),
    }
    values.update(overrides)
    return module.MarketDiscoveryCandidate(**values)


def report(*items: object, generated_at: datetime = GENERATED_AT, cfg: object | None = None) -> Any:
    module = api()
    return module.build_market_discovery_candidate_pool_readiness_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_values(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_float_values(item)


def test_candidate_pool_ranks_valid_polymarket_markets_for_readonly_readiness() -> None:
    module = api()
    result = report(
        candidate(
            market_id="market-thin",
            slug="thin-market",
            question="Will the thin market resolve?",
            category="sports",
            liquidity=d("900.000000"),
            spread=d("0.040000"),
            data_freshness=d("60.000000"),
        ),
        candidate(
            market_id="market-stale",
            slug="stale-market",
            question="Will the stale market resolve?",
            category="crypto",
            liquidity=d("5000.000000"),
            spread=d("0.030000"),
            data_freshness=d("600.000000"),
        ),
        candidate(
            market_id="market-ready",
            slug="ready-market",
            question="Will the ready market resolve?",
            category="politics",
            liquidity=d("5000.000000"),
            spread=d("0.010000"),
            data_freshness=d("10.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "market-discovery-candidate-pool-v0"
    assert result.candidate_count == d("3")
    assert result.ready_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "candidate_pool_ready",
        "data_freshness_stale_blocker",
        "liquidity_below_minimum_attention",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.market_id for row in result.rows) == (
        "market-stale",
        "market-thin",
        "market-ready",
    )
    assert tuple(row.slug for row in result.rows) == (
        "stale-market",
        "thin-market",
        "ready-market",
    )
    assert tuple(row.status for row in result.rows) == ("blocked", "watch", "ready")
    assert tuple(row.readiness_score for row in result.rows) == (
        d("0.250000"),
        d("0.750000"),
        d("1.000000"),
    )

    ready = result.rows[2]
    assert ready.market_id == "market-ready"
    assert ready.question == "Will the ready market resolve?"
    assert ready.category == "politics"
    assert ready.liquidity == d("5000.000000")
    assert ready.spread == d("0.010000")
    assert ready.end_time == GENERATED_AT + timedelta(days=7)
    assert ready.data_freshness == d("10.000000")
    assert ready.seconds_until_end == d("604800.000000")
    assert ready.reason_codes == ("candidate_pool_ready",)
    assert ready.paper_only is True
    assert ready.report_only is True
    assert ready.readonly is True

    payload = module.market_discovery_candidate_pool_readiness_report_payload(result)
    assert payload == result.payload
    assert payload["generated_at"] == "2026-07-12T12:00:00+00:00"
    assert payload["candidate_count"] == "3.000000"
    assert payload["rows"][0]["market_id"] == "market-stale"
    assert payload["rows"][0]["data_freshness"] == "600.000000"
    assert payload["rows"][2]["readiness_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_candidate_pool_preserves_exact_microseconds_for_long_horizons() -> None:
    generated_at = datetime(1, 1, 1, tzinfo=UTC)
    end_time = datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=UTC)
    delta = end_time - generated_at
    expected_seconds = (
        Decimal(delta.days) * d("86400")
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / d("1000000")
    ).quantize(d("0.000001"))

    result = report(
        candidate(end_time=end_time),
        generated_at=generated_at,
    )

    assert result.rows[0].seconds_until_end == expected_seconds


def test_validation_rejects_missing_required_fields_bad_decimals_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="market_id must be a non-empty string"):
        candidate(market_id="")
    with pytest.raises(ValueError, match="slug must be a non-empty string"):
        candidate(slug=StringSubclass("subclass-slug"))
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        candidate(question=" ")
    with pytest.raises(ValueError, match="category must be a non-empty string"):
        candidate(category="")
    with pytest.raises(ValueError, match="liquidity must be a Decimal"):
        candidate(liquidity=2500)
    with pytest.raises(ValueError, match="spread must be a Decimal"):
        candidate(spread=0.02)
    with pytest.raises(ValueError, match="data_freshness must be an exact Decimal"):
        candidate(data_freshness=DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="end_time must be a datetime"):
        candidate(end_time=DatetimeSubclass(2026, 7, 19, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="end_time must be timezone-aware"):
        candidate(end_time=datetime(2026, 7, 19, 12))
    with pytest.raises(ValueError, match="end_time must be after generated_at"):
        report(candidate(end_time=GENERATED_AT))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 12, 12))
    with pytest.raises(ValueError, match="config must be a MarketDiscoveryCandidatePoolConfig"):
        module.build_market_discovery_candidate_pool_readiness_report(
            [candidate()],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate market_id values"):
        report(candidate(), candidate(slug="other-slug"))
    with pytest.raises(ValueError, match="duplicate slug values"):
        report(candidate(), candidate(market_id="market-beta-002"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report(candidate()), readonly=False)


def test_empty_pool_and_expiring_market_report_blockers_without_execution_language() -> None:
    module = api()

    empty = report()
    assert empty.status == "blocked"
    assert empty.candidate_count == ZERO
    assert empty.reason_codes == ("candidate_pool_empty_blocker",)
    assert empty.rows == ()

    expiring = report(
        candidate(
            market_id="market-expiring",
            slug="expiring-market",
            question="Will this expire soon?",
            liquidity=d("5000.000000"),
            spread=d("0.010000"),
            end_time=GENERATED_AT + timedelta(minutes=30),
            data_freshness=d("10.000000"),
        ),
    )
    assert expiring.status == "blocked"
    assert expiring.rows[0].status == "blocked"
    assert expiring.rows[0].seconds_until_end == d("1800.000000")
    assert expiring.rows[0].reason_codes == ("end_time_too_close_blocker",)

    payload_text = json.dumps(
        module.market_discovery_candidate_pool_readiness_report_payload(expiring),
        allow_nan=False,
        sort_keys=True,
    ).lower()
    for forbidden in (
        "wallet",
        "auth",
        "private_key",
        "place_order",
        "create_order",
        "cancel_order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position_size",
    ):
        assert forbidden not in payload_text


def test_public_dataclasses_are_frozen_decimal_only_and_consistency_checked() -> None:
    module = api()
    cfg = config()
    item = candidate()
    result = report(
        item,
        candidate(
            market_id="market-thin",
            slug="thin-market",
            question="Will this thin market resolve?",
            liquidity=d("900.000000"),
        ),
        cfg=cfg,
    )
    row = result.rows[0]

    for klass in (
        module.MarketDiscoveryCandidate,
        module.MarketDiscoveryCandidatePoolConfig,
        module.MarketDiscoveryCandidatePoolReasonCodeCount,
        module.MarketDiscoveryCandidatePoolRow,
        module.MarketDiscoveryCandidatePoolReadinessReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        item.market_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]

    for instance in (cfg, item, row, result, result.reason_code_counts[0]):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if field.name in {"paper_only", "report_only", "readonly", "payload"}:
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="readiness_score must match reason codes"):
        replace(row, readiness_score=d("0.500000"))
    with pytest.raises(ValueError, match="ready_count must match rows"):
        replace(result, ready_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        module.MarketDiscoveryCandidatePoolReadinessReport(
            **{
                **result.__dict__,
                "rows": tuple(reversed(result.rows)),
            },
        )


def test_payload_revalidates_nested_row_consistency() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result.rows[0], "readiness_score", d("0.500000"))

    with pytest.raises(ValueError, match="readiness_score must match reason codes"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_rejects_coherent_row_report_forgery_against_custom_thresholds() -> None:
    module = api()
    result = report(
        candidate(),
        cfg=config(
            min_liquidity=d("3000.000000"),
            max_spread=d("0.010000"),
            max_data_age_seconds=d("20.000000"),
            min_seconds_until_end=d("700000.000000"),
        ),
    )
    row = result.rows[0]
    assert row.reason_codes == (
        "data_freshness_stale_blocker",
        "end_time_too_close_blocker",
        "liquidity_below_minimum_attention",
        "spread_above_maximum_attention",
    )

    object.__setattr__(row, "readiness_score", d("1.000000"))
    object.__setattr__(row, "status", "ready")
    object.__setattr__(row, "reason_codes", ("candidate_pool_ready",))
    object.__setattr__(result, "ready_count", d("1.000000"))
    object.__setattr__(result, "blocked_count", ZERO)
    object.__setattr__(result, "status", "ready")
    object.__setattr__(result, "reason_codes", ("candidate_pool_ready",))
    object.__setattr__(
        result,
        "reason_code_counts",
        (
            module.MarketDiscoveryCandidatePoolReasonCodeCount(
                reason_code="candidate_pool_ready",
                count=d("1.000000"),
                ratio=d("1.000000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="reason_codes must match effective config"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_report_snapshots_effective_config_in_public_payload() -> None:
    module = api()
    cfg = config(
        min_liquidity=d("3000.000000"),
        max_spread=d("0.010000"),
        max_data_age_seconds=d("20.000000"),
        min_seconds_until_end=d("700000.000000"),
    )
    result = report(candidate(), cfg=cfg)

    assert type(result.effective_config) is module.MarketDiscoveryCandidatePoolConfig
    assert result.effective_config == cfg
    assert result.effective_config is not cfg
    assert result.effective_config.paper_only is True
    assert result.effective_config.report_only is True
    assert result.effective_config.readonly is True
    assert result.payload["effective_config"] == {
        "config_version": "market-discovery-candidate-pool-v0",
        "min_liquidity": "3000.000000",
        "max_spread": "0.010000",
        "max_data_age_seconds": "20.000000",
        "min_seconds_until_end": "700000.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    object.__setattr__(cfg, "min_liquidity", d("9999.000000"))
    assert result.effective_config.min_liquidity == d("3000.000000")
    assert result.payload["effective_config"]["min_liquidity"] == "3000.000000"


def test_payload_revalidates_effective_config_exact_type() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result, "effective_config", object())

    with pytest.raises(
        ValueError,
        match="effective_config must be a MarketDiscoveryCandidatePoolConfig",
    ):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("min_liquidity", "1000.000000", "min_liquidity must be a Decimal"),
        ("paper_only", False, "paper_only must be True for effective_config"),
        ("report_only", False, "report_only must be True for effective_config"),
        ("readonly", False, "readonly must be True for effective_config"),
    ),
)
def test_payload_revalidates_effective_config_threshold_types_and_flags(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    module = api()
    result = report(candidate())
    effective_config = config()
    object.__setattr__(effective_config, field_name, bad_value)
    object.__setattr__(result, "effective_config", effective_config)

    with pytest.raises(ValueError, match=message):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_revalidates_nested_row_phase1_flags() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result.rows[0], "paper_only", False)

    with pytest.raises(ValueError, match="paper_only must be True for row"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_revalidates_nested_row_time_derivation() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result.rows[0], "seconds_until_end", d("60.000000"))

    with pytest.raises(ValueError, match="seconds_until_end must match"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_rejects_coherent_row_at_generated_at() -> None:
    module = api()
    result = report(candidate())
    row = result.rows[0]

    object.__setattr__(row, "end_time", GENERATED_AT)
    object.__setattr__(row, "seconds_until_end", ZERO)
    object.__setattr__(row, "readiness_score", d("0.250000"))
    object.__setattr__(row, "status", "blocked")
    object.__setattr__(row, "reason_codes", ("end_time_too_close_blocker",))
    object.__setattr__(result, "ready_count", ZERO)
    object.__setattr__(result, "blocked_count", d("1.000000"))
    object.__setattr__(result, "status", "blocked")
    object.__setattr__(result, "reason_codes", ("end_time_too_close_blocker",))
    object.__setattr__(
        result,
        "reason_code_counts",
        (
            module.MarketDiscoveryCandidatePoolReasonCodeCount(
                reason_code="end_time_too_close_blocker",
                count=d("1.000000"),
                ratio=d("1.000000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="end_time must be after generated_at"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_revalidates_nested_row_value_types() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result.rows[0], "liquidity", "2500.000000")

    with pytest.raises(ValueError, match="liquidity must be a Decimal"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_revalidates_nested_row_derived_value_types_before_sorting() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result.rows[0], "readiness_score", "1.000000")

    with pytest.raises(ValueError, match="readiness_score must be a Decimal"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_revalidates_report_config_version() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result, "config_version", "forged-version")

    with pytest.raises(ValueError, match="config_version must be the supported"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_revalidates_report_generated_at_utc_normalization() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(
        result,
        "generated_at",
        GENERATED_AT.astimezone(timezone(timedelta(hours=8))),
    )

    with pytest.raises(ValueError, match="generated_at must be normalized to UTC"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_revalidates_report_decimal_types() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result, "candidate_count", 1)

    with pytest.raises(ValueError, match="candidate_count must be a Decimal"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


@pytest.mark.parametrize(
    ("target_name", "field_name", "bad_value", "message"),
    (
        ("report", "candidate_count", d("1"), "candidate_count must be normalized"),
        ("row", "liquidity", d("2500"), "liquidity must be normalized"),
        ("row", "readiness_score", d("1"), "readiness_score must be normalized"),
        ("reason_count", "count", d("1"), "count must be normalized"),
        ("reason_count", "ratio", d("1"), "ratio must be normalized"),
        (
            "effective_config",
            "min_liquidity",
            d("1000"),
            "min_liquidity must be normalized",
        ),
    ),
)
def test_payload_rejects_noncanonical_decimal_quantum_across_report_graph(
    target_name: str,
    field_name: str,
    bad_value: Decimal,
    message: str,
) -> None:
    module = api()
    result = report(candidate())
    targets = {
        "report": result,
        "row": result.rows[0],
        "reason_count": result.reason_code_counts[0],
        "effective_config": result.effective_config,
    }
    object.__setattr__(targets[target_name], field_name, bad_value)

    with pytest.raises(ValueError, match=message):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_revalidates_nested_reason_count_decimal_types() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result.reason_code_counts[0], "count", 1)

    with pytest.raises(ValueError, match="count must be a Decimal"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_rejects_noncanonical_rows_container() -> None:
    module = api()
    result = report(candidate())

    object.__setattr__(result, "rows", list(result.rows))

    with pytest.raises(ValueError, match="rows must be a canonical tuple"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


@pytest.mark.parametrize(
    ("target_name", "field_name", "bad_value_factory", "message"),
    (
        (
            "report",
            "reason_codes",
            lambda result: list(result.reason_codes),
            "reason_codes must be a canonical tuple",
        ),
        (
            "report",
            "reason_code_counts",
            lambda result: list(result.reason_code_counts),
            "reason_code_counts must be a canonical tuple",
        ),
        (
            "row",
            "reason_codes",
            lambda result: list(result.rows[0].reason_codes),
            "reason_codes must be a canonical tuple",
        ),
    ),
)
def test_payload_rejects_other_noncanonical_containers(
    target_name: str,
    field_name: str,
    bad_value_factory: Any,
    message: str,
) -> None:
    module = api()
    result = report(candidate())
    target = result if target_name == "report" else result.rows[0]
    object.__setattr__(target, field_name, bad_value_factory(result))

    with pytest.raises(ValueError, match=message):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "status",
            StringSubclass("ready"),
            "status must be a known candidate pool readiness status",
        ),
        (
            "reason_codes",
            TupleSubclass(("candidate_pool_ready",)),
            "reason_codes must be a canonical tuple",
        ),
        (
            "reason_codes",
            (StringSubclass("candidate_pool_ready"),),
            "reason_codes must be a known candidate pool reason code",
        ),
    ),
)
def test_payload_rejects_report_level_equal_but_nonexact_types(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    module = api()
    result = report(candidate())
    object.__setattr__(result, field_name, bad_value)

    with pytest.raises(ValueError, match=message):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_rejects_duplicate_nested_market_identity() -> None:
    module = api()
    result = report(
        candidate(),
        candidate(
            market_id="market-beta-002",
            slug="will-beta-happen",
            question="Will beta happen by Friday?",
        ),
    )

    object.__setattr__(result, "rows", (result.rows[0], result.rows[0]))

    with pytest.raises(ValueError, match="duplicate market_id values"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_payload_rejects_duplicate_nested_slug_identity() -> None:
    module = api()
    result = report(
        candidate(),
        candidate(
            market_id="market-beta-002",
            slug="will-beta-happen",
            question="Will beta happen by Friday?",
        ),
    )
    object.__setattr__(result.rows[1], "slug", result.rows[0].slug)

    with pytest.raises(ValueError, match="duplicate slug values"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


@pytest.mark.parametrize(
    ("target_name", "flag_name"),
    (
        ("report", "paper_only"),
        ("report", "report_only"),
        ("report", "readonly"),
        ("row", "report_only"),
        ("row", "readonly"),
        ("reason_count", "paper_only"),
        ("reason_count", "report_only"),
        ("reason_count", "readonly"),
    ),
)
def test_payload_revalidates_hard_flags_across_nested_report_graph(
    target_name: str,
    flag_name: str,
) -> None:
    module = api()
    result = report(candidate())
    targets = {
        "report": result,
        "row": result.rows[0],
        "reason_count": result.reason_code_counts[0],
    }
    object.__setattr__(targets[target_name], flag_name, False)
    label = "reason_code_count" if target_name == "reason_count" else target_name

    with pytest.raises(ValueError, match=rf"{flag_name} must be True for {label}"):
        module.market_discovery_candidate_pool_readiness_report_payload(result)


def test_source_has_no_network_persistence_float_or_execution_surfaces() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: list[str] = []

    assert "wallet" not in source.lower()
    assert "private_key" not in source.lower()
    assert "place_order" not in source.lower()
    assert "create_order" not in source.lower()
    assert "cancel_order" not in source.lower()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    banned_import_roots = {
        "asyncio",
        "csv",
        "http",
        "jsonlines",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    assert not (set(imported_modules) & banned_import_roots)

    public_api_text = "\n".join(module.__all__).lower()
    for forbidden in (
        "strategy",
        "supabase",
        "scrap",
        "team_memory",
        "cli",
        "execution",
        "auth",
        "trade",
    ):
        assert forbidden not in public_api_text
