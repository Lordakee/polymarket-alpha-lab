from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import ROUND_DOWN, Decimal, localcontext
import hashlib
from importlib import import_module
import inspect
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NaiveTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab."
        "research_market_probability_liquidity_regime_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_REGIME_CONFIG_VERSION
        ),
        "tail_probability_max": d("0.100000"),
        "max_pass_spread_rate": d("0.020000"),
        "max_watch_spread_rate": d("0.050000"),
        "min_pass_depth_score": d("0.700000"),
        "min_watch_depth_score": d("0.400000"),
        "max_pass_cost_rate": d("0.030000"),
        "max_watch_cost_rate": d("0.070000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityLiquidityRegimeConfig(**values)


def observation(label: str = "case-pass", **overrides: object) -> Any:
    module = api()
    values = {
        "case_digest": digest(label),
        "observed_at": GENERATED_AT - timedelta(minutes=5),
        "market_probability": d("0.500000"),
        "spread_rate": d("0.010000"),
        "depth_score": d("0.900000"),
        "cost_rate": d("0.010000"),
        "upstream_reason_codes": ("review_sample",),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityLiquidityRegimeObservation(**values)


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_market_probability_liquidity_regime_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned = deepcopy(payload)
    unsigned.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            unsigned,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    return payload


def test_report_combines_probability_spread_depth_and_cost_into_stable_regimes() -> None:
    module = api()
    blocked = observation(
        "case-block",
        market_probability=d("0.050000"),
        spread_rate=d("0.080000"),
        depth_score=d("0.200000"),
        cost_rate=d("0.090000"),
        upstream_reason_codes=(),
    )
    watched = observation(
        "case-watch",
        market_probability=d("0.950000"),
        spread_rate=d("0.030000"),
        depth_score=d("0.600000"),
        cost_rate=d("0.050000"),
        upstream_reason_codes=(),
    )
    passed = observation()

    forward = build_report(watched, passed, blocked)
    reverse = build_report(blocked, passed, watched)
    offset_time = module.build_research_market_probability_liquidity_regime_report(
        (passed, blocked, watched),
        config=config(),
        generated_at=datetime(
            2026,
            7,
            10,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert type(forward) is module.ResearchMarketProbabilityLiquidityRegimeReport
    assert is_dataclass(forward)
    assert forward.generated_at == GENERATED_AT
    assert forward.status == "block"
    assert forward.observation_count == d("3.000000")
    assert forward.pass_count == d("1.000000")
    assert forward.watch_count == d("1.000000")
    assert forward.block_count == d("1.000000")
    assert forward.tail_count == d("2.000000")
    assert forward.robust_count == d("1.000000")
    assert forward.constrained_count == d("1.000000")
    assert forward.fragile_count == d("1.000000")
    assert forward.manual_review_count == d("2.000000")
    assert forward.average_market_probability == d("0.500000")
    assert forward.average_liquidity_score == d("0.449206")
    assert forward.minimum_depth_score == d("0.200000")
    assert forward.maximum_spread_rate == d("0.080000")
    assert forward.maximum_cost_rate == d("0.090000")
    assert tuple(row.case_digest for row in forward.rows) == (
        digest("case-block"),
        digest("case-watch"),
        digest("case-pass"),
    )
    assert tuple(row.rank for row in forward.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    block_row, watch_row, pass_row = forward.rows
    assert block_row.probability_band == "low_tail"
    assert block_row.probability_extremity_score == d("0.900000")
    assert block_row.spread_quality_score == d("0.000000")
    assert block_row.cost_quality_score == d("0.000000")
    assert block_row.liquidity_score == d("0.066667")
    assert block_row.liquidity_regime == "fragile"
    assert block_row.regime == "low_tail_fragile"
    assert block_row.status == "block"
    assert block_row.manual_review_required is True
    assert block_row.reason_codes == (
        "probability_liquidity_regime_status_block",
        "probability_band_low_tail",
        "liquidity_regime_fragile",
        "spread_block",
        "depth_block",
        "cost_block",
    )

    assert watch_row.probability_band == "high_tail"
    assert watch_row.probability_extremity_score == d("0.900000")
    assert watch_row.spread_quality_score == d("0.400000")
    assert watch_row.cost_quality_score == d("0.285714")
    assert watch_row.liquidity_score == d("0.428571")
    assert watch_row.liquidity_regime == "constrained"
    assert watch_row.regime == "high_tail_constrained"
    assert watch_row.status == "watch"
    assert watch_row.manual_review_required is True
    assert watch_row.reason_codes == (
        "probability_liquidity_regime_status_watch",
        "probability_band_high_tail",
        "liquidity_regime_constrained",
        "spread_watch",
        "depth_watch",
        "cost_watch",
    )

    assert pass_row.probability_band == "central"
    assert pass_row.probability_extremity_score == d("0.000000")
    assert pass_row.spread_quality_score == d("0.800000")
    assert pass_row.cost_quality_score == d("0.857143")
    assert pass_row.liquidity_score == d("0.852381")
    assert pass_row.liquidity_regime == "robust"
    assert pass_row.regime == "central_robust"
    assert pass_row.status == "pass"
    assert pass_row.manual_review_required is False
    assert pass_row.reason_codes == (
        "probability_liquidity_regime_status_pass",
        "probability_band_central",
        "liquidity_regime_robust",
        "review_sample",
    )

    assert forward.reason_codes == (
        "probability_liquidity_regime_report_block",
        "probability_tail_present",
        "liquidity_fragile_present",
        "liquidity_constrained_present",
        "liquidity_robust_present",
        "manual_review_required",
    )
    assert forward.payload == reverse.payload == offset_time.payload
    assert forward.derived_validation_digest == reverse.derived_validation_digest
    assert len(forward.derived_validation_digest) == 64
    int(forward.derived_validation_digest, 16)
    assert forward.paper_only is True
    assert forward.report_only is True
    assert forward.readonly is True


def test_empty_report_blocks_screening_and_has_exact_canonical_payload_schema() -> None:
    module = api()
    empty = build_report()
    payload = module.research_market_probability_liquidity_regime_report_payload(empty)

    assert empty.status == "block"
    assert empty.observation_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.block_count == d("0.000000")
    assert empty.tail_count == d("0.000000")
    assert empty.robust_count == d("0.000000")
    assert empty.constrained_count == d("0.000000")
    assert empty.fragile_count == d("0.000000")
    assert empty.manual_review_count == d("0.000000")
    assert empty.average_market_probability == d("0.000000")
    assert empty.average_liquidity_score == d("0.000000")
    assert empty.minimum_depth_score == d("0.000000")
    assert empty.maximum_spread_rate == d("0.000000")
    assert empty.maximum_cost_rate == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("probability_liquidity_regime_report_empty",)

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "config",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "tail_count",
        "robust_count",
        "constrained_count",
        "fragile_count",
        "manual_review_count",
        "average_market_probability",
        "average_liquidity_score",
        "minimum_depth_score",
        "maximum_spread_rate",
        "maximum_cost_rate",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["config"]) == (
        "config_version",
        "tail_probability_max",
        "max_pass_spread_rate",
        "max_watch_spread_rate",
        "min_pass_depth_score",
        "min_watch_depth_score",
        "max_pass_cost_rate",
        "max_watch_cost_rate",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert payload["generated_at"] == "2026-07-10T12:00:00+00:00"
    assert payload["observation_count"] == "0.000000"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == empty.derived_validation_digest
    assert module.validate_research_market_probability_liquidity_regime_report_payload(
        deepcopy(payload),
    ) == payload
    _assert_json_numeric_surface(payload)
    json.dumps(payload, sort_keys=True)


def test_exact_schema_frozen_decimal_only_and_raw_bounds_are_strict() -> None:
    module = api()
    built = build_report(observation())

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_REGIME_CONFIG_VERSION",
        "ResearchMarketProbabilityLiquidityRegimeConfig",
        "ResearchMarketProbabilityLiquidityRegimeObservation",
        "ResearchMarketProbabilityLiquidityRegimeRow",
        "ResearchMarketProbabilityLiquidityRegimeReasonCodeCount",
        "ResearchMarketProbabilityLiquidityRegimeReport",
        "build_research_market_probability_liquidity_regime_report",
        "research_market_probability_liquidity_regime_report_payload",
        "validate_research_market_probability_liquidity_regime_report_payload",
    )
    assert tuple(field.name for field in fields(module.ResearchMarketProbabilityLiquidityRegimeRow)) == (
        "case_digest",
        "rank",
        "observed_at",
        "market_probability",
        "probability_band",
        "probability_extremity_score",
        "spread_rate",
        "spread_quality_score",
        "depth_score",
        "cost_rate",
        "cost_quality_score",
        "liquidity_score",
        "liquidity_regime",
        "regime",
        "status",
        "manual_review_required",
        "upstream_reason_codes",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )

    for value in (config(), observation(), built.rows[0], *built.reason_code_counts, built):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]
        _assert_decimal_only_dataclass(value)

    with pytest.raises(ValueError, match="market_probability.*between 0 and 1"):
        observation(market_probability=d("1.0000004"))
    with pytest.raises(ValueError, match="spread_rate.*nonnegative"):
        observation(spread_rate=d("-0.0000004"))
    with pytest.raises(ValueError, match="depth_score.*signed zero"):
        observation(depth_score=d("-0"))
    with pytest.raises(ValueError, match="cost_rate.*finite"):
        observation(cost_rate=d("NaN"))
    with pytest.raises(ValueError, match="cost_rate.*finite"):
        observation(cost_rate=d("Infinity"))
    with pytest.raises(ValueError, match="depth_score.*Decimal"):
        observation(depth_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="spread_rate.*Decimal"):
        observation(spread_rate=0.01)
    with pytest.raises(ValueError, match="tail_probability_max.*between 0 and 0.5"):
        config(tail_probability_max=d("0.5000004"))
    with pytest.raises(ValueError, match="generated_at.*datetime"):
        module.build_research_market_probability_liquidity_regime_report(
            (observation(),),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 10, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_research_market_probability_liquidity_regime_report(
            (observation(),),
            config=config(),
            generated_at=datetime(2026, 7, 10, 12, 0),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_research_market_probability_liquidity_regime_report(
            (observation(),),
            config=config(),
            generated_at=datetime(2026, 7, 10, 12, 0, tzinfo=_NaiveTz()),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)


def test_resigned_payload_requires_complete_derived_recomputation_and_exact_schema() -> None:
    module = api()
    built = build_report(
        observation(
            "case-block",
            market_probability=d("0.050000"),
            spread_rate=d("0.080000"),
            depth_score=d("0.200000"),
            cost_rate=d("0.090000"),
            upstream_reason_codes=(),
        ),
    )
    payload = deepcopy(built.payload)

    bad_digest = deepcopy(payload)
    bad_digest["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            bad_digest,
        )

    resigned_status = deepcopy(payload)
    resigned_status["rows"][0]["status"] = "pass"
    resign_payload(resigned_status)
    with pytest.raises(ValueError, match=r"rows\[0\]\.status"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            resigned_status,
        )

    resigned_probability = deepcopy(payload)
    resigned_probability["rows"][0]["market_probability"] = "0.500000"
    resign_payload(resigned_probability)
    with pytest.raises(ValueError, match=r"rows\[0\]\.probability"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            resigned_probability,
        )

    resigned_count = deepcopy(payload)
    resigned_count["observation_count"] = "9.000000"
    resign_payload(resigned_count)
    with pytest.raises(ValueError, match="observation_count"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            resigned_count,
        )

    extra_field = deepcopy(payload)
    extra_field["unexpected"] = "field"
    resign_payload(extra_field)
    with pytest.raises(ValueError, match="exact schema"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            extra_field,
        )

    missing_nested = deepcopy(payload)
    del missing_nested["rows"][0]["liquidity_score"]
    resign_payload(missing_nested)
    with pytest.raises(ValueError, match="exact schema"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            missing_nested,
        )

    numeric = deepcopy(payload)
    numeric["observation_count"] = 1
    with pytest.raises(ValueError, match="canonical Decimal string"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            numeric,
        )

    signed_zero = deepcopy(payload)
    signed_zero["rows"][0]["spread_rate"] = "-0.000000"
    resign_payload(signed_zero)
    with pytest.raises(ValueError, match="signed zero"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            signed_zero,
        )

    downgraded = deepcopy(payload)
    downgraded["readonly"] = False
    resign_payload(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            downgraded,
        )


def test_decimal_results_ignore_hostile_process_context() -> None:
    item = observation(
        "context-independent",
        market_probability=d("0.876520"),
        spread_rate=d("0.012345"),
        depth_score=d("0.812345"),
        cost_rate=d("0.023456"),
        upstream_reason_codes=(),
    )
    cfg = config(tail_probability_max=d("0.123456"))
    expected = build_report(item, cfg=cfg).payload

    with localcontext() as hostile_context:
        hostile_context.prec = 4
        hostile_context.rounding = ROUND_DOWN
        actual = build_report(item, cfg=cfg).payload

    assert actual == expected


def test_payload_canonicalizes_key_order_and_requires_exact_string_keys() -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)

    reordered = {
        key: payload[key]
        for key in reversed(tuple(payload))
    }
    resign_payload(reordered)
    assert (
        module.validate_research_market_probability_liquidity_regime_report_payload(
            reordered,
        )
        == payload
    )

    nested_reordered = deepcopy(payload)
    nested_reordered["rows"][0] = {
        key: nested_reordered["rows"][0][key]
        for key in reversed(tuple(nested_reordered["rows"][0]))
    }
    resign_payload(nested_reordered)
    assert (
        module.validate_research_market_probability_liquidity_regime_report_payload(
            nested_reordered,
        )
        == payload
    )

    non_exact_key = deepcopy(payload)
    status = non_exact_key.pop("status")
    non_exact_key[_StringSubclass("status")] = status
    resign_payload(non_exact_key)
    with pytest.raises(ValueError, match="exact schema"):
        module.validate_research_market_probability_liquidity_regime_report_payload(
            non_exact_key,
        )


@pytest.mark.parametrize(
    "private_reason_code",
    (
        "user_id_present",
        "email_address_present",
        "session_identifier_present",
        "account_identifier_present",
    ),
)
def test_private_identifiers_are_rejected_from_public_reason_codes(
    private_reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public content"):
        observation(upstream_reason_codes=(private_reason_code,))


def test_complete_tie_break_is_input_order_independent() -> None:
    items = tuple(
        observation(
            label,
            market_probability=d("0.500000"),
            spread_rate=d("0.010000"),
            depth_score=d("0.900000"),
            cost_rate=d("0.010000"),
            upstream_reason_codes=(),
        )
        for label in ("tie-c", "tie-a", "tie-b")
    )

    forward = build_report(*items)
    reverse = build_report(*reversed(items))
    expected_digests = tuple(sorted(item.case_digest for item in items))

    assert tuple(row.case_digest for row in forward.rows) == expected_digests
    assert tuple(row.rank for row in forward.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert forward.payload == reverse.payload


def test_resigned_payload_rederives_every_public_derived_surface() -> None:
    module = api()
    built = build_report(
        observation(
            "derived-block",
            market_probability=d("0.050000"),
            spread_rate=d("0.080000"),
            depth_score=d("0.200000"),
            cost_rate=d("0.090000"),
            upstream_reason_codes=(),
        ),
        observation("derived-pass", upstream_reason_codes=()),
    )
    payload = deepcopy(built.payload)
    tampered_payloads: list[dict[str, Any]] = []

    row_score = deepcopy(payload)
    row_score["rows"][0]["liquidity_score"] = "0.500000"
    tampered_payloads.append(row_score)

    row_reason = deepcopy(payload)
    row_reason["rows"][0]["reason_codes"] = [
        "probability_liquidity_regime_status_watch",
    ]
    tampered_payloads.append(row_reason)

    row_rank = deepcopy(payload)
    row_rank["rows"][0]["rank"] = "2.000000"
    tampered_payloads.append(row_rank)

    report_status = deepcopy(payload)
    report_status["status"] = "watch"
    tampered_payloads.append(report_status)

    report_reason = deepcopy(payload)
    report_reason["reason_codes"] = [
        "probability_liquidity_regime_report_watch",
    ]
    tampered_payloads.append(report_reason)

    report_count = deepcopy(payload)
    report_count["observation_count"] = "3.000000"
    tampered_payloads.append(report_count)

    report_aggregate = deepcopy(payload)
    report_aggregate["average_liquidity_score"] = "0.500000"
    tampered_payloads.append(report_aggregate)

    reason_aggregate = deepcopy(payload)
    reason_aggregate["reason_code_counts"][0]["row_count"] = "9.000000"
    tampered_payloads.append(reason_aggregate)

    reranked = deepcopy(payload)
    reranked["rows"] = list(reversed(reranked["rows"]))
    for index, row in enumerate(reranked["rows"], start=1):
        row["rank"] = f"{index}.000000"
    tampered_payloads.append(reranked)

    for tampered in tampered_payloads:
        resign_payload(tampered)
        with pytest.raises(ValueError):
            module.validate_research_market_probability_liquidity_regime_report_payload(
                tampered,
            )


def test_direct_tampering_duplicate_cases_and_unstable_rows_are_rejected() -> None:
    module = api()
    built = build_report(
        observation(
            "case-block",
            market_probability=d("0.050000"),
            spread_rate=d("0.080000"),
            depth_score=d("0.200000"),
            cost_rate=d("0.090000"),
            upstream_reason_codes=(),
        ),
        observation(),
    )

    with pytest.raises(ValueError, match="unique"):
        build_report(observation(), observation())
    with pytest.raises(ValueError, match="liquidity_score"):
        replace(built.rows[0], liquidity_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="pass")
    with pytest.raises(ValueError, match="deterministic sorting"):
        replace(built, rows=tuple(reversed(built.rows)))
    with pytest.raises(ValueError, match="observation_count"):
        replace(built, observation_count=d("9.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    custom = config(
        tail_probability_max=d("0.200000"),
        max_pass_spread_rate=d("0.030000"),
    )
    custom_report = build_report(
        observation(
            "custom",
            market_probability=d("0.150000"),
            spread_rate=d("0.025000"),
            upstream_reason_codes=(),
        ),
        cfg=custom,
    )
    assert custom_report.rows[0].probability_band == "low_tail"
    assert custom_report.rows[0].liquidity_regime == "robust"
    assert custom_report.rows[0].status == "watch"
    assert (
        module.validate_research_market_probability_liquidity_regime_report_payload(
            deepcopy(custom_report.payload),
        )
        == custom_report.payload
    )


def test_source_is_pure_and_has_no_external_side_effect_capabilities() -> None:
    module = api()
    source = inspect.getsource(module)
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_probability_liquidity_regime_report.py"
    )
    tree = ast.parse(source_path.read_text())
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.partition(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    assert not {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    } & imports
    assert not {"connect", "open", "request", "run", "send"} & calls
    assert "position_size" not in source


def _assert_json_numeric_surface(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_json_numeric_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_json_numeric_surface(item)
        return
    assert type(value) not in (Decimal, float, int)


def _assert_decimal_only_dataclass(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            assert item.is_finite()
            assert not (item.is_zero() and item.is_signed())
        elif is_dataclass(item):
            _assert_decimal_only_dataclass(item)
        elif isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    _assert_decimal_only_dataclass(nested)
                elif isinstance(nested, Decimal):
                    assert type(nested) is Decimal
