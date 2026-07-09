from __future__ import annotations

import ast
import hashlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
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
        "research_market_probability_liquidity_conflict_gate_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "case_digest": digest("case-pass"),
        "model_probability": d("0.550000"),
        "market_probability": d("0.530000"),
        "spread_width": d("0.005000"),
        "depth_score": d("0.900000"),
        "liquidity_score": d("0.900000"),
        "fee_drag": d("0.003000"),
        "volatility_score": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.MarketProbabilityLiquidityConflictGateSignal(**values)


def report(rows: list[object] | tuple[object, ...]) -> Any:
    module = api()
    return module.build_research_market_probability_liquidity_conflict_gate_report(
        rows,
        generated_at=GENERATED_AT,
    )


def test_conflict_gate_scores_sorts_and_uses_only_pass_watch_block_statuses() -> None:
    module = api()
    passed = signal()
    watched = signal(
        case_digest=digest("case-watch"),
        model_probability=d("0.680000"),
        market_probability=d("0.580000"),
        spread_width=d("0.015000"),
        depth_score=d("0.550000"),
        liquidity_score=d("0.500000"),
        fee_drag=d("0.010000"),
        volatility_score=d("0.400000"),
    )
    blocked = signal(
        case_digest=digest("case-block"),
        model_probability=d("0.850000"),
        market_probability=d("0.500000"),
        spread_width=d("0.040000"),
        depth_score=d("0.250000"),
        liquidity_score=d("0.300000"),
        fee_drag=d("0.020000"),
        volatility_score=d("0.850000"),
    )

    conflict_report = report([passed, watched, blocked])
    repeated_report = report([blocked, passed, watched])

    assert type(conflict_report) is module.MarketProbabilityLiquidityConflictGateReport
    assert is_dataclass(conflict_report)
    assert conflict_report.generated_at == GENERATED_AT
    assert conflict_report.config_version == (
        module.DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_CONFLICT_GATE_CONFIG_VERSION
    )
    assert conflict_report.gate_status == "block"
    assert conflict_report.case_count == d("3.000000")
    assert conflict_report.pass_count == d("1.000000")
    assert conflict_report.watch_count == d("1.000000")
    assert conflict_report.block_count == d("1.000000")
    assert conflict_report.average_probability_gap == d("0.156667")
    assert conflict_report.max_adjusted_probability_gap == d("0.290000")
    assert conflict_report.average_liquidity_shortfall_score == d("0.433333")
    assert conflict_report.max_conflict_score == d("0.828750")
    assert [row.case_digest for row in conflict_report.rows] == [
        digest("case-block"),
        digest("case-watch"),
        digest("case-pass"),
    ]

    assert conflict_report.rows[0].gate_status == "block"
    assert conflict_report.rows[0].probability_gap == d("0.350000")
    assert conflict_report.rows[0].adjusted_probability_gap == d("0.290000")
    assert conflict_report.rows[0].liquidity_shortfall_score == d("0.725000")
    assert conflict_report.rows[0].conflict_score == d("0.828750")
    assert conflict_report.rows[0].manual_review_required is True
    assert conflict_report.rows[0].reason_codes == (
        "conflict_gate_block",
        "probability_gap_block",
        "spread_width_watch",
        "depth_block",
        "liquidity_quality_block",
        "fee_drag_watch",
        "volatility_block",
        "conflict_score_block",
    )

    assert conflict_report.rows[1].gate_status == "watch"
    assert conflict_report.rows[1].probability_gap == d("0.100000")
    assert conflict_report.rows[1].adjusted_probability_gap == d("0.075000")
    assert conflict_report.rows[1].liquidity_shortfall_score == d("0.475000")
    assert conflict_report.rows[1].conflict_score == d("0.331250")
    assert conflict_report.rows[1].manual_review_required is True
    assert conflict_report.rows[1].reason_codes == (
        "conflict_gate_watch",
        "probability_gap_watch",
        "depth_watch",
        "liquidity_quality_watch",
        "conflict_score_watch",
    )

    assert conflict_report.rows[2].gate_status == "pass"
    assert conflict_report.rows[2].probability_gap == d("0.020000")
    assert conflict_report.rows[2].adjusted_probability_gap == d("0.012000")
    assert conflict_report.rows[2].liquidity_shortfall_score == d("0.100000")
    assert conflict_report.rows[2].conflict_score == d("0.068000")
    assert conflict_report.rows[2].manual_review_required is False
    assert conflict_report.rows[2].reason_codes == ("conflict_gate_pass",)
    assert (
        conflict_report.derived_validation_digest
        == repeated_report.derived_validation_digest
    )
    assert len(conflict_report.derived_validation_digest) == 64
    assert set(conflict_report.derived_validation_digest) <= set("0123456789abcdef")
    assert conflict_report.paper_only is True
    assert conflict_report.report_only is True
    assert conflict_report.readonly is True


def test_empty_input_is_report_only_and_public_payload_is_tamper_evident() -> None:
    module = api()
    empty_report = report([])

    assert empty_report.gate_status == "pass"
    assert empty_report.case_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.reason_code_counts == ()
    assert empty_report.average_probability_gap == d("0.000000")
    assert empty_report.max_adjusted_probability_gap == d("0.000000")
    assert empty_report.average_liquidity_shortfall_score == d("0.000000")
    assert empty_report.max_conflict_score == d("0.000000")

    payload = module.research_market_probability_liquidity_conflict_gate_report_payload(
        empty_report,
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["gate_status"] == "pass"
    assert payload["case_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == empty_report.derived_validation_digest
    assert not _contains_float(payload)
    _assert_public_payload_safe(payload)

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["gate_status"] = "block"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["gate_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_probability_liquidity_conflict_gate_report_payload(
            tampered,
        )


def test_custom_config_drives_row_reason_code_validation() -> None:
    module = api()
    custom_config = module.MarketProbabilityLiquidityConflictGateConfig(
        watch_probability_gap=d("0.100000"),
        block_probability_gap=d("0.250000"),
    )

    custom_report = (
        module.build_research_market_probability_liquidity_conflict_gate_report(
            [
                signal(
                    case_digest=digest("custom-config-pass"),
                    model_probability=d("0.600000"),
                    market_probability=d("0.520000"),
                    spread_width=d("0.000000"),
                    depth_score=d("0.950000"),
                    liquidity_score=d("0.950000"),
                    fee_drag=d("0.000000"),
                    volatility_score=d("0.000000"),
                ),
            ],
            generated_at=GENERATED_AT,
            config=custom_config,
        )
    )

    assert custom_report.gate_status == "pass"
    assert custom_report.rows[0].adjusted_probability_gap == d("0.080000")
    assert custom_report.rows[0].reason_codes == ("conflict_gate_pass",)
    assert custom_report.rows[0].manual_review_required is False
    assert custom_report.reason_code_counts[0].reason_code == "conflict_gate_pass"
    module.research_market_probability_liquidity_conflict_gate_report_payload(
        custom_report,
    )


def test_payload_keeps_private_references_outside_public_surface() -> None:
    module = api()
    raw_private_reference = (
        "raw_candidate=alpha candidate_id=cid market_id=mid "
        "market_slug=slug question text source_url=https://example.invalid/a "
        "source_text secret dsn table token wallet order trade"
    )
    conflict_report = report(
        [
            signal(
                case_digest=digest(raw_private_reference),
                model_probability=d("0.720000"),
                market_probability=d("0.610000"),
            ),
        ],
    )

    payload = module.research_market_probability_liquidity_conflict_gate_report_payload(
        conflict_report,
    )
    rendered_payload = json.dumps(payload, sort_keys=True)

    assert payload["rows"][0]["case_digest"] == digest(raw_private_reference)
    assert raw_private_reference not in rendered_payload
    for fragment in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "https://example.invalid/a",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        assert fragment not in rendered_payload.lower()
    _assert_public_payload_safe(payload)


def test_validation_is_strict_frozen_decimal_only_and_flag_locked() -> None:
    module = api()
    base_signal = signal()
    conflict_report = report([base_signal])

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_CONFLICT_GATE_CONFIG_VERSION",
        "MarketProbabilityLiquidityConflictGateConfig",
        "MarketProbabilityLiquidityConflictGateSignal",
        "MarketProbabilityLiquidityConflictGateRow",
        "MarketProbabilityLiquidityConflictGateReasonCodeCount",
        "MarketProbabilityLiquidityConflictGateReport",
        "build_research_market_probability_liquidity_conflict_gate_report",
        "research_market_probability_liquidity_conflict_gate_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        base_signal.case_digest = digest("mutated")  # type: ignore[misc]
    with pytest.raises(ValueError, match="case_digest"):
        signal(case_digest="not-a-digest")
    with pytest.raises(ValueError, match="model_probability"):
        signal(model_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_probability"):
        signal(market_probability=d("1.500000"))
    with pytest.raises(ValueError, match="depth_score"):
        signal(depth_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="spread_width"):
        signal(spread_width=d("-0.001000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_probability_liquidity_conflict_gate_report(
            [base_signal],
            generated_at=_DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_research_market_probability_liquidity_conflict_gate_report(
            [base_signal],
            generated_at=datetime(2026, 7, 9),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_research_market_probability_liquidity_conflict_gate_report(
            [base_signal],
            generated_at=datetime(2026, 7, 9, tzinfo=_NaiveTz()),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(base_signal, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(conflict_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(conflict_report, derived_validation_digest="0" * 64)

    for value in _walk_public_values(conflict_report):
        if isinstance(value, Decimal):
            assert type(value) is Decimal
        if type(value) is int or isinstance(value, float):
            raise AssertionError(f"public numeric value is not Decimal: {value!r}")


def test_rejects_duplicate_cases_bad_reason_codes_and_unsafe_public_payload() -> None:
    module = api()
    base = signal()
    with pytest.raises(ValueError, match="unique"):
        report([base, base])

    blocked_row = report(
        [
            signal(
                case_digest=digest("blocked"),
                model_probability=d("0.850000"),
                market_probability=d("0.500000"),
                depth_score=d("0.250000"),
                liquidity_score=d("0.300000"),
                volatility_score=d("0.850000"),
            ),
        ],
    ).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            blocked_row,
            reason_codes=("conflict_gate_block", "volatility_block"),
            derived_validation_digest="",
        )

    payload = module.research_market_probability_liquidity_conflict_gate_report_payload(
        report([base]),
    )
    with pytest.raises(ValueError, match="readonly"):
        module.research_market_probability_liquidity_conflict_gate_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_probability_liquidity_conflict_gate_report_payload(
            {**payload, "candidate_id": "abc"},
        )
    with pytest.raises(ValueError, match="numeric|Decimal"):
        module.research_market_probability_liquidity_conflict_gate_report_payload(
            {**payload, "case_count": 1},
        )


def test_source_file_has_no_io_side_effect_or_live_private_surface() -> None:
    module = api()
    source = inspect.getsource(module)
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_probability_liquidity_conflict_gate_report.py"
    )
    tree = ast.parse(source_path.read_text())
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.partition(".")[0])

    assert not {
        "asyncio",
        "http",
        "os",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    } & imports
    lowered = source.lower()
    for forbidden in (
        "auth",
        "database_url",
        "dsn",
        "execute_trade",
        "live trading",
        "market_id",
        "market_slug",
        "order",
        "place_order",
        "position_size",
        "raw_candidate",
        "raw_market",
        "recommendation",
        "sizing",
        "source_text",
        "source_url",
        "table_name",
        "token",
        "trade",
        "wallet",
    ):
        assert forbidden not in lowered


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def _assert_public_payload_safe(value: object) -> None:
    banned_payload_fragments = (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(fragment in lowered for fragment in banned_payload_fragments)
            _assert_public_payload_safe(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_payload_safe(item)


def _walk_public_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            values.extend(_walk_public_values(getattr(value, field.name)))
    elif isinstance(value, tuple):
        for item in value:
            values.extend(_walk_public_values(item))
    return tuple(values)
