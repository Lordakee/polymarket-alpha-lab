from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_probability_momentum_cost_drag_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_probability_momentum_cost_drag_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "research-market-probability-momentum-cost-drag-report-v1",
        "watch_net_momentum": d("0.020000"),
        "pass_net_momentum": d("0.060000"),
        "watch_total_cost_drag": d("0.030000"),
        "block_total_cost_drag": d("0.080000"),
        "watch_component_drag": d("0.015000"),
        "block_component_drag": d("0.040000"),
    }
    values.update(overrides)
    return module.MarketProbabilityMomentumCostDragConfig(**values)


def observation(
    private_candidate_reference: str = "candidate-block-private-id",
    *,
    private_market_reference: str = "market-id-123/will-this-question-resolve",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=20),
    prior_probability: Decimal = d("0.500000"),
    current_probability: Decimal = d("0.620000"),
    fee_drag: Decimal = d("0.025000"),
    spread_drag: Decimal = d("0.025000"),
    slippage_buffer: Decimal = d("0.030000"),
    liquidity_depth_drag: Decimal = d("0.025000"),
    confidence_haircut: Decimal = d("0.025000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketProbabilityMomentumCostDragObservation(
        private_candidate_reference=private_candidate_reference,
        private_market_reference=private_market_reference,
        observed_at=observed_at,
        prior_probability=prior_probability,
        current_probability=current_probability,
        fee_drag=fee_drag,
        spread_drag=spread_drag,
        slippage_buffer=slippage_buffer,
        liquidity_depth_drag=liquidity_depth_drag,
        confidence_haircut=confidence_haircut,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    observations: tuple[Any, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_probability_momentum_cost_drag_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def signal_digest(private_candidate_reference: str, private_market_reference: str) -> str:
    value = f"{private_candidate_reference}\x1f{private_market_reference}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def number_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) in (float, int, Decimal):
        return (path or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(number_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(number_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def payload_with_fresh_digest(payload: dict[str, Any]) -> dict[str, Any]:
    refreshed = deepcopy(payload)
    digest_payload = dict(refreshed)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    refreshed["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return refreshed


def test_builds_probability_momentum_cost_drag_report_for_research_only() -> None:
    built = report(
        (
            observation(
                "signal-pass-private-id",
                private_market_reference="market-pass/will-pass-question-resolve",
                fee_drag=d("0.005000"),
                spread_drag=d("0.004000"),
                slippage_buffer=d("0.003000"),
                liquidity_depth_drag=d("0.004000"),
                confidence_haircut=d("0.004000"),
            ),
            observation(),
            observation(
                "signal-watch-private-id",
                private_market_reference="market-watch/will-watch-question-resolve",
                current_probability=d("0.575000"),
                fee_drag=d("0.010000"),
                spread_drag=d("0.016000"),
                slippage_buffer=d("0.004000"),
                liquidity_depth_drag=d("0.005000"),
                confidence_haircut=d("0.005000"),
            ),
        ),
    )

    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.block_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.pass_count == d("1.000000")
    assert built.average_gross_momentum_abs == d("0.105000")
    assert built.average_total_cost_drag == d("0.063333")
    assert built.average_net_momentum_abs == d("0.045000")
    assert built.max_gross_momentum_abs == d("0.120000")
    assert built.max_total_cost_drag == d("0.130000")
    assert built.max_net_momentum_abs == d("0.100000")
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    assert [(row.signal_digest, row.status, row.net_momentum_abs) for row in built.rows] == [
        (
            signal_digest(
                "candidate-block-private-id",
                "market-id-123/will-this-question-resolve",
            ),
            "block",
            d("0.000000"),
        ),
        (
            signal_digest(
                "signal-watch-private-id",
                "market-watch/will-watch-question-resolve",
            ),
            "watch",
            d("0.035000"),
        ),
        (
            signal_digest(
                "signal-pass-private-id",
                "market-pass/will-pass-question-resolve",
            ),
            "pass",
            d("0.100000"),
        ),
    ]

    blocked = built.rows[0]
    assert blocked.triage_rank == d("1.000000")
    assert blocked.gross_momentum_abs == d("0.120000")
    assert blocked.momentum_direction == "up"
    assert blocked.total_cost_drag == d("0.130000")
    assert blocked.reason_codes == (
        "probability_momentum_cost_drag_confidence_haircut_watch",
        "probability_momentum_cost_drag_costs_overwhelm_momentum",
        "probability_momentum_cost_drag_direction_up",
        "probability_momentum_cost_drag_fee_drag_watch",
        "probability_momentum_cost_drag_liquidity_depth_drag_watch",
        "probability_momentum_cost_drag_net_momentum_block",
        "probability_momentum_cost_drag_slippage_buffer_watch",
        "probability_momentum_cost_drag_spread_drag_watch",
        "probability_momentum_cost_drag_status_block",
        "probability_momentum_cost_drag_total_drag_block",
    )

    watch = built.rows[1]
    assert watch.reason_codes == (
        "probability_momentum_cost_drag_direction_up",
        "probability_momentum_cost_drag_net_momentum_watch",
        "probability_momentum_cost_drag_partly_meaningful_after_drag",
        "probability_momentum_cost_drag_spread_drag_watch",
        "probability_momentum_cost_drag_status_watch",
        "probability_momentum_cost_drag_total_drag_watch",
    )

    counts_by_code = {item.reason_code: item.count for item in built.reason_code_counts}
    assert counts_by_code["probability_momentum_cost_drag_direction_up"] == d("3.000000")
    assert counts_by_code["probability_momentum_cost_drag_status_block"] == d("1.000000")
    assert counts_by_code["probability_momentum_cost_drag_status_watch"] == d("1.000000")
    assert counts_by_code["probability_momentum_cost_drag_status_pass"] == d("1.000000")
    assert built.reason_code_counts == tuple(
        sorted(built.reason_code_counts, key=lambda item: (-item.count, item.reason_code)),
    )
    assert built.reason_codes == tuple(sorted(built.reason_codes))


def test_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    module = api()
    observations = (
        observation(
            "signal-zeta-private-id",
            private_market_reference="market-zeta/will-zeta-question-resolve",
            upstream_reason_codes=("probability_momentum_cost_drag_public_vendor",),
        ),
        observation(
            "signal-alpha-private-id",
            private_market_reference="market-alpha/will-alpha-question-resolve",
            fee_drag=d("0.005000"),
            spread_drag=d("0.004000"),
            slippage_buffer=d("0.003000"),
            liquidity_depth_drag=d("0.004000"),
            confidence_haircut=d("0.004000"),
        ),
    )

    first = module.research_market_probability_momentum_cost_drag_report_payload(
        report(observations),
    )
    second = module.research_market_probability_momentum_cost_drag_report_payload(
        report(tuple(reversed(observations))),
    )

    assert first == second
    assert json.dumps(first, sort_keys=True)
    assert number_paths(first) == ()
    assert not any(isinstance(value, Decimal) for value in walk_values(first))
    assert first["row_count"] == "2.000000"
    assert first["paper_only"] is True
    assert first["report_only"] is True
    assert first["readonly"] is True
    assert first["rows"][0]["signal_digest"] == signal_digest(
        "signal-zeta-private-id",
        "market-zeta/will-zeta-question-resolve",
    )
    assert first["rows"][0]["reason_codes"] == sorted(first["rows"][0]["reason_codes"])

    digest_payload = dict(first)
    provided_digest = digest_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert provided_digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert (
        module.validate_research_market_probability_momentum_cost_drag_report_payload(first)
        == first
    )

    tampered = dict(first)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_probability_momentum_cost_drag_report_payload(
            tampered,
        )


def test_public_payload_excludes_private_market_references_and_action_surfaces() -> None:
    module = api()
    built = report(
        (
            observation(
                private_candidate_reference="candidate-block-private-id",
                private_market_reference=(
                    "market-id-123/will-this-market-question-resolve"
                    "?token=secret"
                ),
            ),
        ),
    )

    payload = module.research_market_probability_momentum_cost_drag_report_payload(built)
    rendered = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "candidate-block-private-id",
        "market-id-123",
        "will-this-market-question-resolve",
        "token",
        "secret",
        "private_candidate_reference",
        "private_market_reference",
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "wallet",
        "order",
        "trade",
        "live",
        "recommend",
        "sizing",
    ):
        assert forbidden not in rendered

    unsafe_report = replace(built)
    object.__setattr__(
        unsafe_report,
        "reason_codes",
        ("probability_momentum_cost_drag_status_pass", "raw_candidate_id"),
    )
    object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_probability_momentum_cost_drag_report_payload(unsafe_report)


def test_payload_validator_rejects_numeric_values_nested_bad_flags_and_extra_surfaces() -> None:
    module = api()
    payload = module.research_market_probability_momentum_cost_drag_report_payload(
        report((observation(),)),
    )

    numeric_payload = payload_with_fresh_digest({**payload, "row_count": 1})
    with pytest.raises(ValueError, match="JSON numeric"):
        module.validate_research_market_probability_momentum_cost_drag_report_payload(
            numeric_payload,
        )

    nested_bad_flag = deepcopy(payload)
    nested_bad_flag["rows"][0]["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_probability_momentum_cost_drag_report_payload(
            payload_with_fresh_digest(nested_bad_flag),
        )

    candidate_surface = payload_with_fresh_digest(
        {**payload, "candidate_reference": "candidate-123"},
    )
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_market_probability_momentum_cost_drag_report_payload(
            candidate_surface,
        )

    execution_surface = payload_with_fresh_digest(
        {**payload, "execution_surface": "enabled"},
    )
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_market_probability_momentum_cost_drag_report_payload(
            execution_surface,
        )

    table_surface = payload_with_fresh_digest({**payload, "table": "research_inputs"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_market_probability_momentum_cost_drag_report_payload(
            table_surface,
        )


def test_rejects_float_inputs_subclasses_bad_datetimes_future_rows_and_bad_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="current_probability"):
        observation(current_probability=d("NaN"))

    with pytest.raises(ValueError, match="prior_probability"):
        observation(prior_probability=_DecimalSubclass("0.500000"))

    with pytest.raises(ValueError, match="fee_drag"):
        observation(fee_drag=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="watch_net_momentum"):
        config(watch_net_momentum=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="block_total_cost_drag"):
        config(block_total_cost_drag=d("0.020000"))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 8, 18, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 8, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        report((observation(readonly=False),))

    built = report((observation(),))
    unsafe_report = replace(built)
    object.__setattr__(unsafe_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_probability_momentum_cost_drag_report_payload(
            unsafe_report,
        )

    with pytest.raises(ValueError, match="report"):
        module.research_market_probability_momentum_cost_drag_report_payload(
            {"bad": "value"},
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report((observation(),))

    for item in (config(), observation(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]

    public_classes = (
        module.MarketProbabilityMomentumCostDragConfig,
        module.MarketProbabilityMomentumCostDragObservation,
        module.MarketProbabilityMomentumCostDragRow,
        module.MarketProbabilityMomentumCostDragReasonCodeCount,
        module.MarketProbabilityMomentumCostDragReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        assert all(
            field.type not in (int, float)
            for field in fields(klass)
            if field.name not in {"paper_only", "report_only", "readonly"}
        )
        with pytest.raises(TypeError, match="subclass"):
            type(f"Bad{klass.__name__}", (klass,), {})


def test_empty_report_blocks_as_missing_inputs_with_valid_digest() -> None:
    module = api()
    built = report(())
    payload = module.research_market_probability_momentum_cost_drag_report_payload(built)

    assert built.status == "block"
    assert built.input_count == d("0.000000")
    assert built.row_count == d("0.000000")
    assert built.block_count == d("0.000000")
    assert built.reason_codes == ("probability_momentum_cost_drag_missing_inputs",)
    assert built.reason_code_counts[0].reason_code == (
        "probability_momentum_cost_drag_missing_inputs"
    )
    assert built.rows == ()
    assert payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert (
        module.validate_research_market_probability_momentum_cost_drag_report_payload(
            payload,
        )
        == payload
    )


def test_module_has_no_execution_auth_durable_or_action_surface() -> None:
    module = api()
    module_path = Path(__file__).resolve().parents[1] / MODULE_PATH
    source = module_path.read_text(encoding="utf-8").lower()
    tree = ast.parse(source)

    for token in (
        "private_key",
        "api_key",
        "requests",
        "httpx",
        "urllib",
        "urlopen",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "redis",
        "os.environ",
        "getenv",
        "open(",
        "read_text",
        "write_text",
        "path(",
        "connect(",
        "execute(",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "wallet",
        "trade",
        "recommendation",
        "sizing",
    ):
        assert token not in source

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    exported = module_path.read_text(encoding="utf-8").split("__all__ = (", 1)[1].split(")", 1)[0]
    assert "build_research_market_probability_momentum_cost_drag_report" in exported
    assert "research_market_probability_momentum_cost_drag_report_payload" in exported
    assert "validate_research_market_probability_momentum_cost_drag_report_payload" in exported
