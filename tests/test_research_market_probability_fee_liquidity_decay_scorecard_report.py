from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_probability_fee_liquidity_decay_scorecard_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_probability_fee_liquidity_decay_scorecard_report.py",
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
            module.DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_LIQUIDITY_DECAY_SCORECARD_REPORT_CONFIG_VERSION
        ),
        "watch_total_fee_cost_ratio": d("0.030000"),
        "block_total_fee_cost_ratio": d("0.080000"),
        "watch_probability_decay_ratio": d("0.040000"),
        "block_probability_decay_ratio": d("0.100000"),
        "watch_liquidity_decay_ratio": d("0.200000"),
        "block_liquidity_decay_ratio": d("0.500000"),
        "watch_liquidity_score_floor": d("0.550000"),
        "block_liquidity_score_floor": d("0.300000"),
        "pass_score_floor": d("0.700000"),
        "watch_score_floor": d("0.400000"),
        "fee_drag_weight": d("0.250000"),
        "probability_decay_weight": d("0.250000"),
        "liquidity_quality_weight": d("0.250000"),
        "liquidity_decay_weight": d("0.250000"),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig(**values)


def observation(
    public_signal_ref: str = "pass-public-signal",
    *,
    observed_at: datetime = GENERATED_AT,
    baseline_probability: Decimal = d("0.600000"),
    current_probability: Decimal = d("0.590000"),
    fee_cost_ratio: Decimal = d("0.005000"),
    spread_cost_ratio: Decimal = d("0.010000"),
    liquidity_score: Decimal = d("0.850000"),
    reference_liquidity_score: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation(
        public_signal_ref=public_signal_ref,
        observed_at=observed_at,
        baseline_probability=baseline_probability,
        current_probability=current_probability,
        fee_cost_ratio=fee_cost_ratio,
        spread_cost_ratio=spread_cost_ratio,
        liquidity_score=liquidity_score,
        reference_liquidity_score=reference_liquidity_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_probability_fee_liquidity_decay_scorecard_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def payload_without_digest(payload: dict[str, object]) -> dict[str, object]:
    trimmed = dict(payload)
    trimmed.pop("derived_validation_digest", None)
    return trimmed


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(
            item for nested in value.values() for item in walk_payload_values(nested)
        )
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def test_scores_pass_watch_block_rows_with_decimal_only_scorecard_math() -> None:
    module = api()
    built = report(
        observation("pass-public-signal"),
        observation(
            "watch-public-signal",
            baseline_probability=d("0.600000"),
            current_probability=d("0.540000"),
            fee_cost_ratio=d("0.010000"),
            spread_cost_ratio=d("0.025000"),
            liquidity_score=d("0.600000"),
            reference_liquidity_score=d("0.850000"),
        ),
        observation(
            "block-public-signal",
            baseline_probability=d("0.650000"),
            current_probability=d("0.500000"),
            fee_cost_ratio=d("0.030000"),
            spread_cost_ratio=d("0.060000"),
            liquidity_score=d("0.250000"),
            reference_liquidity_score=d("0.850000"),
            reason_codes=("manual_review",),
        ),
    )

    assert type(built) is module.ResearchMarketProbabilityFeeLiquidityDecayScorecardReport
    assert is_dataclass(built)
    assert module.STATUSES == ("pass", "watch", "block")
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.total_fee_cost_watch_count == d("2.000000")
    assert built.probability_decay_watch_count == d("2.000000")
    assert built.liquidity_decay_watch_count == d("2.000000")
    assert built.liquidity_score_watch_count == d("1.000000")
    assert built.max_total_fee_cost_ratio == d("0.090000")
    assert built.max_probability_decay_ratio == d("0.150000")
    assert built.max_liquidity_decay_ratio == d("0.600000")
    assert built.min_liquidity_score == d("0.250000")
    assert built.average_probability_fee_liquidity_decay_score == d("0.481250")
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    blocked, watched, passed = built.rows
    assert tuple(row.public_signal_ref for row in built.rows) == (
        "block-public-signal",
        "watch-public-signal",
        "pass-public-signal",
    )
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")

    assert blocked.probability_decay_ratio == d("0.150000")
    assert blocked.total_fee_cost_ratio == d("0.090000")
    assert blocked.liquidity_decay_ratio == d("0.600000")
    assert blocked.fee_drag_score == ZERO
    assert blocked.probability_decay_score == ZERO
    assert blocked.liquidity_decay_score == ZERO
    assert blocked.probability_fee_liquidity_decay_score == d("0.062500")
    assert blocked.reason_codes == (
        "input_manual_review",
        "probability_fee_liquidity_decay_scorecard_block",
        "probability_fee_liquidity_decay_scorecard_fee_cost_block",
        "probability_fee_liquidity_decay_scorecard_liquidity_decay_block",
        "probability_fee_liquidity_decay_scorecard_liquidity_score_block",
        "probability_fee_liquidity_decay_scorecard_probability_decay_block",
        "probability_fee_liquidity_decay_scorecard_score_block",
    )

    assert watched.probability_decay_ratio == d("0.060000")
    assert watched.total_fee_cost_ratio == d("0.035000")
    assert watched.liquidity_decay_ratio == d("0.250000")
    assert watched.fee_drag_score == d("0.562500")
    assert watched.probability_decay_score == d("0.400000")
    assert watched.liquidity_decay_score == d("0.500000")
    assert watched.probability_fee_liquidity_decay_score == d("0.515625")
    assert watched.reason_codes == (
        "probability_fee_liquidity_decay_scorecard_fee_cost_watch",
        "probability_fee_liquidity_decay_scorecard_liquidity_decay_watch",
        "probability_fee_liquidity_decay_scorecard_probability_decay_watch",
        "probability_fee_liquidity_decay_scorecard_score_watch",
        "probability_fee_liquidity_decay_scorecard_watch",
    )

    assert passed.probability_decay_ratio == d("0.010000")
    assert passed.total_fee_cost_ratio == d("0.015000")
    assert passed.liquidity_decay_ratio == d("0.050000")
    assert passed.fee_drag_score == d("0.812500")
    assert passed.probability_decay_score == d("0.900000")
    assert passed.liquidity_decay_score == d("0.900000")
    assert passed.probability_fee_liquidity_decay_score == d("0.865625")
    assert passed.reason_codes == (
        "probability_fee_liquidity_decay_scorecard_clear",
    )


def test_empty_inputs_block_with_report_only_reason_count() -> None:
    module = api()
    built = report()

    assert built.status == "block"
    assert built.input_count == ZERO
    assert built.row_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.total_fee_cost_watch_count == ZERO
    assert built.probability_decay_watch_count == ZERO
    assert built.liquidity_decay_watch_count == ZERO
    assert built.liquidity_score_watch_count == ZERO
    assert built.max_total_fee_cost_ratio == ZERO
    assert built.max_probability_decay_ratio == ZERO
    assert built.max_liquidity_decay_ratio == ZERO
    assert built.min_liquidity_score == ZERO
    assert built.average_probability_fee_liquidity_decay_score == ZERO
    assert built.reason_codes == (
        "probability_fee_liquidity_decay_scorecard_no_inputs",
    )
    assert built.reason_code_counts == (
        module.ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount(
            reason_code="probability_fee_liquidity_decay_scorecard_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert built.rows == ()


def test_public_payload_digest_is_deterministic_decimal_only_and_redacted() -> None:
    module = api()
    first = report(
        observation("beta-public-signal", current_probability=d("0.580000")),
        observation("alpha-public-signal"),
    )
    second = report(
        observation("alpha-public-signal"),
        observation("beta-public-signal", current_probability=d("0.580000")),
    )

    first_payload = (
        module.research_market_probability_fee_liquidity_decay_scorecard_report_payload(
            first,
        )
    )
    second_payload = (
        module.research_market_probability_fee_liquidity_decay_scorecard_report_payload(
            second,
        )
    )
    digest = (
        module.research_market_probability_fee_liquidity_decay_scorecard_report_digest(
            first,
        )
    )
    encoded = json.dumps(first_payload, sort_keys=True).lower()

    assert first == second
    assert first.public_payload == first_payload
    assert first_payload == second_payload
    assert digest == hashlib.sha256(
        json.dumps(
            payload_without_digest(first_payload),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert digest == first_payload["derived_validation_digest"]
    assert digest == first.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["input_count"] == "2.000000"
    assert first_payload["rows"][0]["public_signal_ref"] == "alpha-public-signal"
    assert first_payload["rows"][0]["probability_fee_liquidity_decay_score"] == (
        "0.865625"
    )
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(type(value) is int for value in walk_payload_values(first_payload))
    for raw_fragment in (
        "raw-candidate",
        "raw-market",
        "raw question",
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "network",
        "auth",
        "order",
        "trading",
        "sizing",
        "recommendation",
        "https://",
        "example.test",
    ):
        assert raw_fragment not in encoded


def test_public_decimal_outputs_normalize_negative_zero() -> None:
    module = api()
    built = report(
        observation(
            "negative-zero-public-signal",
            baseline_probability=d("0.500000"),
            current_probability=d("0.5000004"),
            fee_cost_ratio=d("-0.0000004"),
            spread_cost_ratio=d("-0.0000004"),
        ),
    )

    payload = module.research_market_probability_fee_liquidity_decay_scorecard_report_payload(
        built,
    )
    encoded = json.dumps(payload, sort_keys=True)
    row = built.rows[0]

    assert format(row.fee_cost_ratio, "f") == "0.000000"
    assert format(row.spread_cost_ratio, "f") == "0.000000"
    assert format(row.probability_decay_ratio, "f") == "0.000000"
    assert format(row.total_fee_cost_ratio, "f") == "0.000000"
    assert "-0.000000" not in encoded


def test_digest_validation_rejects_report_and_nested_payload_tampering() -> None:
    module = api()
    built = report(observation("tamper-public-signal"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    object.__setattr__(
        built.rows[0],
        "probability_fee_liquidity_decay_score",
        ZERO,
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_probability_fee_liquidity_decay_scorecard_report_payload(
            built,
        )


def test_frozen_dataclasses_hard_flags_and_decimal_only_validation() -> None:
    module = api()
    built = report(observation("frozen-public-signal"))

    for public_type in (
        module.ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig,
        module.ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation,
        module.ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount,
        module.ResearchMarketProbabilityFeeLiquidityDecayScorecardReport,
        module.ResearchMarketProbabilityFeeLiquidityDecayScorecardRow,
    ):
        assert is_dataclass(public_type)

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].probability_fee_liquidity_decay_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="watch_total_fee_cost_ratio"):
        config(watch_total_fee_cost_ratio=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="baseline_probability"):
        observation(baseline_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="current_probability"):
        observation(current_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_signal_ref"):
        observation(public_signal_ref="raw-candidate-001")
    with pytest.raises(ValueError, match="public_signal_ref"):
        observation(public_signal_ref="https://example.test/path?token=secret")
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation("aware-public-signal"),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))

    row = built.rows[0]
    with pytest.raises(ValueError, match="status"):
        module.ResearchMarketProbabilityFeeLiquidityDecayScorecardRow(
            public_signal_ref=row.public_signal_ref,
            observed_at=row.observed_at,
            baseline_probability=row.baseline_probability,
            current_probability=row.current_probability,
            probability_decay_ratio=row.probability_decay_ratio,
            fee_cost_ratio=row.fee_cost_ratio,
            spread_cost_ratio=row.spread_cost_ratio,
            total_fee_cost_ratio=row.total_fee_cost_ratio,
            liquidity_score=row.liquidity_score,
            reference_liquidity_score=row.reference_liquidity_score,
            liquidity_decay_ratio=row.liquidity_decay_ratio,
            fee_drag_score=row.fee_drag_score,
            probability_decay_score=row.probability_decay_score,
            liquidity_decay_score=row.liquidity_decay_score,
            probability_fee_liquidity_decay_score=row.probability_fee_liquidity_decay_score,
            status="blocked",
            reason_codes=row.reason_codes,
        )

    for item in (built, *built.rows, *built.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_exports_and_static_forbidden_surface_are_exact() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_LIQUIDITY_DECAY_SCORECARD_REPORT_CONFIG_VERSION",
        "STATUSES",
        "ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig",
        "ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation",
        "ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount",
        "ResearchMarketProbabilityFeeLiquidityDecayScorecardReport",
        "ResearchMarketProbabilityFeeLiquidityDecayScorecardRow",
        "build_research_market_probability_fee_liquidity_decay_scorecard_report",
        "research_market_probability_fee_liquidity_decay_scorecard_report_digest",
        "research_market_probability_fee_liquidity_decay_scorecard_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "live trading",
        "trading",
        "sizing",
        "recommendation",
        "requests",
        "http://",
        "https://",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "private_key",
        "api_key",
        "secret",
        "client",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
