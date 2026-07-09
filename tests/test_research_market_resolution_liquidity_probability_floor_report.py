from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_resolution_liquidity_probability_floor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "unit-v1",
        "pass_floor_threshold": d("0.620000"),
        "block_floor_threshold": d("0.400000"),
        "pass_liquidity_depth_score": d("0.700000"),
        "block_liquidity_depth_score": d("0.250000"),
        "pass_resolution_confidence_score": d("0.650000"),
        "block_resolution_confidence_score": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchMarketResolutionLiquidityProbabilityFloorConfig(**values)


def observation(
    *,
    observed_at: datetime | None = None,
    observed_probability: str = "0.700000",
    liquidity_probability_floor: str = "0.650000",
    resolution_probability_floor: str = "0.680000",
    liquidity_depth_score: str = "0.800000",
    resolution_confidence_score: str = "0.750000",
    evidence_freshness_score: str = "0.900000",
):
    module = api()
    return module.ResearchMarketResolutionLiquidityProbabilityFloorObservation(
        observed_at=observed_at or (GENERATED_AT - timedelta(minutes=15)),
        observed_probability=d(observed_probability),
        liquidity_probability_floor=d(liquidity_probability_floor),
        resolution_probability_floor=d(resolution_probability_floor),
        liquidity_depth_score=d(liquidity_depth_score),
        resolution_confidence_score=d(resolution_confidence_score),
        evidence_freshness_score=d(evidence_freshness_score),
    )


def build_report(*observations: object):
    module = api()
    return module.build_research_market_resolution_liquidity_probability_floor_report(
        observations,
        config=config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def refreshed_digest(payload: dict[str, object]) -> dict[str, object]:
    refreshed = dict(payload)
    refreshed["derived_validation_digest"] = canonical_digest(refreshed)
    return refreshed


def assert_no_float_or_decimal_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is Decimal:
        raise AssertionError(f"unexpected public Decimal value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_or_decimal_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_or_decimal_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_public_leakage(payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, sort_keys=True)
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live_trading",
        "sizing",
        "recommend",
        "notional",
    )
    lowered = encoded.lower()
    for fragment in forbidden_fragments:
        assert fragment not in lowered


def test_builds_report_statuses_counts_and_deterministic_digest_payload() -> None:
    module = api()
    report = build_report(
        observation(
            observed_probability="0.710000",
            liquidity_probability_floor="0.660000",
            resolution_probability_floor="0.700000",
            liquidity_depth_score="0.850000",
            resolution_confidence_score="0.760000",
        ),
        observation(
            observed_probability="0.610000",
            liquidity_probability_floor="0.570000",
            resolution_probability_floor="0.590000",
            liquidity_depth_score="0.500000",
            resolution_confidence_score="0.550000",
        ),
        observation(
            observed_probability="0.390000",
            liquidity_probability_floor="0.420000",
            resolution_probability_floor="0.410000",
            liquidity_depth_score="0.200000",
            resolution_confidence_score="0.450000",
        ),
    )

    assert report.report_status == "block"
    assert report.input_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.minimum_effective_probability_floor == d("0.390000")
    assert report.average_effective_probability_floor == d("0.540000")
    assert tuple(row.floor_status for row in report.rows) == ("block", "watch", "pass")
    assert len(report.derived_validation_digest) == 64
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)

    payload = module.research_market_resolution_liquidity_probability_floor_report_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["input_count"] == "3"
    assert payload["block_count"] == "1"
    assert payload["rows"][0]["analysis_rank"] == "1"
    assert payload["rows"][0]["floor_status"] == "block"
    assert payload["rows"][2]["floor_status"] == "pass"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["derived_validation_digest"] == canonical_digest(
        payload["rows"][0],
    )
    assert_no_float_or_decimal_values(payload)
    assert_no_public_leakage(payload)
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            report,
        ),
        sort_keys=True,
    )


def test_empty_report_is_watch_report_only_and_digest_checked() -> None:
    module = api()
    report = build_report()

    assert report.report_status == "watch"
    assert report.input_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.minimum_effective_probability_floor is None
    assert report.average_effective_probability_floor is None
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.research_market_resolution_liquidity_probability_floor_report_payload(
        report,
    )

    assert payload["report_status"] == "watch"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert_no_public_leakage(payload)


def test_payload_revalidates_digest_decimal_only_and_public_safety() -> None:
    module = api()
    report = build_report(observation())
    payload = module.research_market_resolution_liquidity_probability_floor_report_payload(
        report,
    )

    tampered = dict(payload)
    tampered["pass_count"] = "0"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="Decimal"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "report_status": "watch",
                "score": 1,
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="float"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "report_status": "watch",
                "score": 0.5,
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="unsafe|surface"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "report_status": "watch",
                "source_url": "https://example.invalid/?token=secret",
                "derived_validation_digest": "0" * 64,
            },
        )

    unsafe_execution_surface: dict[str, object] = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "report_status": "watch",
        "execution_surface": "disabled",
    }
    unsafe_execution_surface["derived_validation_digest"] = canonical_digest(
        unsafe_execution_surface,
    )
    with pytest.raises(ValueError, match="unsafe|surface"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            unsafe_execution_surface,
        )


def test_public_payload_requires_exact_report_and_row_schemas() -> None:
    module = api()
    payload = module.research_market_resolution_liquidity_probability_floor_report_payload(
        build_report(observation()),
    )

    extra_report_field = refreshed_digest({**payload, "unexpected": "value"})
    with pytest.raises(ValueError, match="schema|fields"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            extra_report_field,
        )

    missing_report_field = dict(payload)
    missing_report_field.pop("average_effective_probability_floor")
    with pytest.raises(ValueError, match="schema|fields"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            refreshed_digest(missing_report_field),
        )

    extra_row_field = dict(payload)
    extra_row = dict(extra_row_field["rows"][0])
    extra_row["unexpected"] = "value"
    extra_row_field["rows"] = [refreshed_digest(extra_row)]
    with pytest.raises(ValueError, match="schema|fields"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            refreshed_digest(extra_row_field),
        )

    missing_row_field = dict(payload)
    missing_row = dict(missing_row_field["rows"][0])
    missing_row.pop("evidence_freshness_score")
    missing_row_field["rows"] = [refreshed_digest(missing_row)]
    with pytest.raises(ValueError, match="schema|fields"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            refreshed_digest(missing_row_field),
        )


def test_public_payload_revalidates_row_and_report_semantics_after_redigest() -> None:
    module = api()
    payload = module.research_market_resolution_liquidity_probability_floor_report_payload(
        build_report(observation()),
    )

    invalid_row_payload = dict(payload)
    invalid_row = dict(invalid_row_payload["rows"][0])
    invalid_row["effective_probability_floor"] = "0.123456"
    invalid_row_payload["rows"] = [refreshed_digest(invalid_row)]
    with pytest.raises(ValueError, match="effective_probability_floor"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            refreshed_digest(invalid_row_payload),
        )

    invalid_report_payload = dict(payload)
    invalid_report_payload["pass_count"] = "0"
    invalid_report_payload["watch_count"] = "1"
    invalid_report_payload["report_status"] = "watch"
    with pytest.raises(ValueError, match="count|report_status"):
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            refreshed_digest(invalid_report_payload),
        )


def test_reducer_and_digest_are_independent_of_input_iteration_order() -> None:
    module = api()
    first = observation(evidence_freshness_score="0.800000")
    second = observation(evidence_freshness_score="0.900000")

    forward = module.build_research_market_resolution_liquidity_probability_floor_report(
        (first, second),
        config=config(),
        generated_at=GENERATED_AT,
    )
    reverse = module.build_research_market_resolution_liquidity_probability_floor_report(
        (second, first),
        config=config(),
        generated_at=GENERATED_AT,
    )

    forward_payload = (
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            forward,
        )
    )
    reverse_payload = (
        module.research_market_resolution_liquidity_probability_floor_report_payload(
            reverse,
        )
    )
    assert forward_payload == reverse_payload
    assert forward.derived_validation_digest == reverse.derived_validation_digest


def test_reducer_is_independent_of_ambient_decimal_context() -> None:
    module = api()
    observations = (
        observation(
            observed_probability="0.610000",
            liquidity_probability_floor="0.610000",
            resolution_probability_floor="0.610000",
        ),
        observation(
            observed_probability="0.620000",
            liquidity_probability_floor="0.620000",
            resolution_probability_floor="0.620000",
        ),
        observation(
            observed_probability="0.640000",
            liquidity_probability_floor="0.640000",
            resolution_probability_floor="0.640000",
        ),
    )
    expected = module.build_research_market_resolution_liquidity_probability_floor_report(
        observations,
        config=config(),
        generated_at=GENERATED_AT,
    )

    with localcontext() as decimal_context:
        decimal_context.prec = 3
        decimal_context.rounding = ROUND_DOWN
        actual = (
            module.build_research_market_resolution_liquidity_probability_floor_report(
                observations,
                config=config(),
                generated_at=GENERATED_AT,
            )
        )

    assert actual == expected
    assert actual.average_effective_probability_floor == d("0.623333")


def test_dataclasses_are_frozen_decimal_only_and_status_limited() -> None:
    module = api()
    cfg = config()
    obs = observation()
    report = build_report(obs)
    row = report.rows[0]

    for value in (cfg, obs, row, report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(row, floor_status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(report, report_status="blocked")
    with pytest.raises(ValueError, match="observed_probability"):
        module.ResearchMarketResolutionLiquidityProbabilityFloorObservation(
            observed_at=GENERATED_AT,
            observed_probability=_DecimalSubclass("0.700000"),
            liquidity_probability_floor=d("0.650000"),
            resolution_probability_floor=d("0.680000"),
            liquidity_depth_score=d("0.800000"),
            resolution_confidence_score=d("0.750000"),
            evidence_freshness_score=d("0.900000"),
        )

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_market_resolution_liquidity_probability_floor_report(
            (obs,),
            config=cfg,
            generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=MissingOffsetTz()),
        )


def test_public_dataclasses_are_final_exact_types() -> None:
    module = api()

    for class_name in (
        "ResearchMarketResolutionLiquidityProbabilityFloorConfig",
        "ResearchMarketResolutionLiquidityProbabilityFloorObservation",
        "ResearchMarketResolutionLiquidityProbabilityFloorRow",
        "ResearchMarketResolutionLiquidityProbabilityFloorReport",
    ):
        public_class = getattr(module, class_name)
        with pytest.raises(TypeError, match="subclass"):
            type(f"Derived{class_name}", (public_class,), {})


def test_module_scope_is_pure_report_only_without_live_surfaces() -> None:
    module = api()

    assert module.__all__ == (
        "ResearchMarketResolutionLiquidityProbabilityFloorConfig",
        "ResearchMarketResolutionLiquidityProbabilityFloorObservation",
        "ResearchMarketResolutionLiquidityProbabilityFloorReport",
        "ResearchMarketResolutionLiquidityProbabilityFloorRow",
        "build_research_market_resolution_liquidity_probability_floor_report",
        "research_market_resolution_liquidity_probability_floor_report_payload",
    )

    public_field_names = {
        field.name
        for public_name in module.__all__
        if is_dataclass(getattr(module, public_name, None))
        for field in fields(getattr(module, public_name))
    }
    for forbidden_fragment in (
        "candidate_id",
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
        "live_trading",
        "sizing",
        "recommend",
        "execution",
    ):
        assert all(forbidden_fragment not in name for name in public_field_names)

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "urllib",
    }
    forbidden_call_names = {
        "cancel",
        "connect",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "send",
        "submit",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("pass_floor_threshold", d("1.000001")),
        ("block_floor_threshold", d("-0.000001")),
        ("pass_liquidity_depth_score", 1),
        ("block_liquidity_depth_score", 0.1),
    ),
)
def test_config_rejects_out_of_range_or_non_decimal_values(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        config(**{field_name: bad_value})
