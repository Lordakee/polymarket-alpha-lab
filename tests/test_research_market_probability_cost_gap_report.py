from __future__ import annotations

import ast
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
    "src/polymarket_alpha_lab/research_market_probability_cost_gap_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_probability_cost_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "research-market-probability-cost-gap-report-v1",
        "watch_probability_gap": d("0.050000"),
        "block_probability_gap": d("0.150000"),
        "watch_total_cost_drag": d("0.030000"),
        "block_total_cost_drag": d("0.080000"),
        "watch_component_cost_drag": d("0.015000"),
        "block_component_cost_drag": d("0.040000"),
    }
    values.update(overrides)
    return module.MarketProbabilityCostGapConfig(**values)


def observation(
    raw_candidate_id: str = "candidate-block",
    *,
    raw_market_reference: str = "market-123/will-this-question-resolve",
    raw_source_reference: str = "https://example.test/source?token=secret",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=20),
    model_probability: Decimal = d("0.670000"),
    observed_market_probability: Decimal = d("0.500000"),
    fee_cost_drag: Decimal = d("0.020000"),
    spread_cost_drag: Decimal = d("0.020000"),
    depth_cost_drag: Decimal = d("0.025000"),
    latency_cost_drag: Decimal = d("0.020000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketProbabilityCostGapObservation(
        raw_candidate_id=raw_candidate_id,
        raw_market_reference=raw_market_reference,
        raw_source_reference=raw_source_reference,
        observed_at=observed_at,
        model_probability=model_probability,
        observed_market_probability=observed_market_probability,
        fee_cost_drag=fee_cost_drag,
        spread_cost_drag=spread_cost_drag,
        depth_cost_drag=depth_cost_drag,
        latency_cost_drag=latency_cost_drag,
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
    return module.build_research_market_probability_cost_gap_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def candidate_digest(raw_candidate_id: str) -> str:
    return hashlib.sha256(raw_candidate_id.encode("utf-8")).hexdigest()


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


def test_builds_probability_cost_gap_report_for_analyst_triage_only() -> None:
    built = report(
        (
            observation("candidate-pass", model_probability=d("0.520000"), fee_cost_drag=d("0.002000"), spread_cost_drag=d("0.002000"), depth_cost_drag=d("0.002000"), latency_cost_drag=d("0.002000")),
            observation("candidate-block"),
            observation("candidate-watch", model_probability=d("0.570000"), fee_cost_drag=d("0.010000"), spread_cost_drag=d("0.015000"), depth_cost_drag=d("0.005000"), latency_cost_drag=d("0.005000")),
        ),
    )

    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.block_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.pass_count == d("1.000000")
    assert built.average_probability_gap_abs == d("0.086667")
    assert built.average_total_cost_drag == d("0.042667")
    assert built.max_probability_gap_abs == d("0.170000")
    assert built.max_total_cost_drag == d("0.085000")
    assert built.max_cost_adjusted_gap_abs == d("0.085000")
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    assert [(row.candidate_digest, row.status, row.total_cost_drag) for row in built.rows] == [
        (candidate_digest("candidate-block"), "block", d("0.085000")),
        (candidate_digest("candidate-watch"), "watch", d("0.035000")),
        (candidate_digest("candidate-pass"), "pass", d("0.008000")),
    ]

    blocked = built.rows[0]
    assert blocked.triage_rank == d("1.000000")
    assert blocked.probability_gap_abs == d("0.170000")
    assert blocked.probability_gap_direction == "model_above_market"
    assert blocked.cost_adjusted_gap_abs == d("0.085000")
    assert blocked.reason_codes == (
        "probability_cost_gap_cost_adjusted_gap_positive",
        "probability_cost_gap_depth_drag_elevated",
        "probability_cost_gap_fee_drag_elevated",
        "probability_cost_gap_gap_block",
        "probability_cost_gap_latency_drag_elevated",
        "probability_cost_gap_model_above_market",
        "probability_cost_gap_spread_drag_elevated",
        "probability_cost_gap_status_block",
        "probability_cost_gap_total_cost_drag_block",
    )

    watch = built.rows[1]
    assert watch.status == "watch"
    assert watch.reason_codes == (
        "probability_cost_gap_cost_adjusted_gap_positive",
        "probability_cost_gap_gap_watch",
        "probability_cost_gap_model_above_market",
        "probability_cost_gap_spread_drag_elevated",
        "probability_cost_gap_status_watch",
        "probability_cost_gap_total_cost_drag_watch",
    )

    counts_by_code = {item.reason_code: item.count for item in built.reason_code_counts}
    assert counts_by_code["probability_cost_gap_model_above_market"] == d("3.000000")
    assert counts_by_code["probability_cost_gap_cost_adjusted_gap_positive"] == d("3.000000")
    assert counts_by_code["probability_cost_gap_status_block"] == d("1.000000")
    assert built.reason_code_counts == tuple(
        sorted(built.reason_code_counts, key=lambda item: (-item.count, item.reason_code)),
    )
    assert built.reason_codes == tuple(sorted(built.reason_codes))


def test_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    module = api()
    observations = (
        observation("candidate-zeta", upstream_reason_codes=("probability_cost_gap_vendor_public",)),
        observation("candidate-alpha", model_probability=d("0.520000"), fee_cost_drag=d("0.002000"), spread_cost_drag=d("0.002000"), depth_cost_drag=d("0.002000"), latency_cost_drag=d("0.002000")),
    )

    first = module.research_market_probability_cost_gap_report_payload(report(observations))
    second = module.research_market_probability_cost_gap_report_payload(
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
    assert first["rows"][0]["candidate_digest"] == candidate_digest("candidate-zeta")
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
    assert module.validate_research_market_probability_cost_gap_report_payload(first) == first

    tampered = dict(first)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_probability_cost_gap_report_payload(tampered)


def test_public_payload_excludes_raw_candidate_market_source_and_sensitive_text() -> None:
    module = api()
    built = report(
        (
            observation(
                raw_candidate_id="candidate-block-private-id",
                raw_market_reference="market-id-123/will-this-market-question-resolve",
                raw_source_reference="https://example.test/source?token=secret",
            ),
        ),
    )

    payload = module.research_market_probability_cost_gap_report_payload(built)
    rendered = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "candidate-block-private-id",
        "market-id-123",
        "will-this-market-question-resolve",
        "https://example.test",
        "source?token",
        "secret",
        "raw_candidate_id",
        "raw_market_reference",
        "raw_source_reference",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden not in rendered

    unsafe_report = replace(built)
    object.__setattr__(
        unsafe_report,
        "reason_codes",
        ("probability_cost_gap_status_pass", "raw_candidate_id"),
    )
    object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_probability_cost_gap_report_payload(unsafe_report)


def test_rejects_float_inputs_subclasses_bad_datetimes_future_rows_and_bad_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="model_probability"):
        observation(model_probability=d("NaN"))

    with pytest.raises(ValueError, match="observed_market_probability"):
        observation(observed_market_probability=_DecimalSubclass("0.500000"))

    with pytest.raises(ValueError, match="fee_cost_drag"):
        observation(fee_cost_drag=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="watch_probability_gap"):
        config(watch_probability_gap=1)  # type: ignore[arg-type]

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
        module.research_market_probability_cost_gap_report_payload(unsafe_report)

    with pytest.raises(ValueError, match="report"):
        module.research_market_probability_cost_gap_report_payload({"bad": "value"})


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report((observation(),))

    for item in (config(), observation(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]

    public_classes = (
        module.MarketProbabilityCostGapConfig,
        module.MarketProbabilityCostGapObservation,
        module.MarketProbabilityCostGapRow,
        module.MarketProbabilityCostGapReasonCodeCount,
        module.MarketProbabilityCostGapReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        assert all(
            field.type not in (int, float)
            for field in fields(klass)
            if field.name not in {"paper_only", "report_only", "readonly"}
        )


def test_empty_report_blocks_as_missing_inputs_with_valid_digest() -> None:
    module = api()
    built = report(())
    payload = module.research_market_probability_cost_gap_report_payload(built)

    assert built.status == "block"
    assert built.input_count == d("0.000000")
    assert built.row_count == d("0.000000")
    assert built.block_count == d("0.000000")
    assert built.reason_codes == ("probability_cost_gap_missing_inputs",)
    assert built.reason_code_counts[0].reason_code == "probability_cost_gap_missing_inputs"
    assert built.rows == ()
    assert payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert module.validate_research_market_probability_cost_gap_report_payload(payload) == payload


def test_module_has_no_live_execution_auth_durable_or_action_surface() -> None:
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
    assert "build_research_market_probability_cost_gap_report" in exported
    assert "research_market_probability_cost_gap_report_payload" in exported
    assert "validate_research_market_probability_cost_gap_report_payload" in exported
