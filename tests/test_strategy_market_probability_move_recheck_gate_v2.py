from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 50, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_NAME = "polymarket_alpha_lab.strategy_market_probability_move_recheck_gate_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_market_probability_move_recheck_gate_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"module missing: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def unsafe_text(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_MARKET_PROBABILITY_MOVE_RECHECK_GATE_V2_CONFIG_VERSION
        ),
        "max_clear_probability_velocity_per_hour": d("0.060000"),
        "max_watch_probability_velocity_per_hour": d("0.120000"),
        "max_clear_evidence_gap_probability": d("0.030000"),
        "max_watch_evidence_gap_probability": d("0.070000"),
        "min_clear_official_source_update_score": d("0.700000"),
        "min_watch_official_source_update_score": d("0.400000"),
        "min_clear_liquidity_movement_score": d("0.700000"),
        "min_watch_liquidity_movement_score": d("0.400000"),
        "min_clear_specialist_confidence_score": d("0.750000"),
        "min_watch_specialist_confidence_score": d("0.500000"),
        "max_clear_resolution_horizon_hours": d("168.000000"),
        "max_watch_resolution_horizon_hours": d("720.000000"),
        "min_clear_support_score": d("0.700000"),
        "min_watch_support_score": d("0.450000"),
        "evidence_alignment_weight": d("0.250000"),
        "official_source_update_weight": d("0.200000"),
        "liquidity_movement_weight": d("0.200000"),
        "specialist_confidence_weight": d("0.200000"),
        "resolution_horizon_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.StrategyMarketProbabilityMoveRecheckGateV2Config(**values)


def snapshot(**overrides: object) -> Any:
    module = api()
    values = {
        "market_slug": "probability-clear-market",
        "condition_id": "condition-clear",
        "observed_at": OBSERVED_AT,
        "previous_market_probability": d("0.500000"),
        "current_market_probability": d("0.530000"),
        "elapsed_minutes": d("60.000000"),
        "evidence_probability_delta": d("0.030000"),
        "official_source_update_score": d("0.800000"),
        "liquidity_movement_score": d("0.800000"),
        "specialist_confidence_score": d("0.800000"),
        "resolution_horizon_hours": d("24.000000"),
        "source_config_version": "probability-move-snapshot-v0",
    }
    values.update(overrides)
    return module.StrategyMarketProbabilityMoveRecheckGateV2Snapshot(**values)


def report(
    *values: object,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_market_probability_move_recheck_gate_v2_report(
        values,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_public_numeric(value: object) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, int, float)):
        raise AssertionError(f"unexpected public numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)


def test_recheck_report_forces_recheck_when_probability_moves_faster_than_evidence_support() -> None:
    result = report(
        snapshot(
            market_slug="z-clear",
            condition_id="condition-clear",
            current_market_probability=d("0.530000"),
            evidence_probability_delta=d("0.030000"),
            official_source_update_score=d("0.800000"),
            liquidity_movement_score=d("0.800000"),
            specialist_confidence_score=d("0.800000"),
            resolution_horizon_hours=d("24.000000"),
        ),
        snapshot(
            market_slug="m-watch",
            condition_id="condition-watch",
            current_market_probability=d("0.580000"),
            evidence_probability_delta=d("0.050000"),
            official_source_update_score=d("0.650000"),
            liquidity_movement_score=d("0.650000"),
            specialist_confidence_score=d("0.700000"),
            resolution_horizon_hours=d("240.000000"),
        ),
        snapshot(
            market_slug="a-recheck",
            condition_id="condition-recheck",
            previous_market_probability=d("0.520000"),
            current_market_probability=d("0.700000"),
            evidence_probability_delta=d("0.050000"),
            official_source_update_score=d("0.300000"),
            liquidity_movement_score=d("0.250000"),
            specialist_confidence_score=d("0.300000"),
            resolution_horizon_hours=d("1000.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-market-probability-move-recheck-gate-v2"
    assert result.market_count == d("3.000000")
    assert result.clear_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.recheck_required_count == d("1.000000")
    assert result.max_market_probability_delta == d("0.180000")
    assert result.max_probability_velocity_per_hour == d("0.180000")
    assert result.max_evidence_gap_probability == d("0.130000")
    assert result.min_support_score == d("0.239445")
    assert result.gate_status == "recheck_required"
    assert result.recommended_next_step == "force_report_only_probability_move_recheck"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.market_slug for row in result.rows) == (
        "a-recheck",
        "m-watch",
        "z-clear",
    )
    recheck_row, watch_row, clear_row = result.rows

    assert recheck_row.market_probability_delta == d("0.180000")
    assert recheck_row.probability_velocity_per_hour == d("0.180000")
    assert recheck_row.evidence_alignment_score == d("0.277778")
    assert recheck_row.evidence_gap_probability == d("0.130000")
    assert recheck_row.resolution_horizon_justification_score == d("0.000000")
    assert recheck_row.support_score == d("0.239445")
    assert recheck_row.gate_status == "recheck_required"
    assert recheck_row.reason_codes == (
        "probability_move_velocity_above_recheck",
        "probability_move_evidence_gap_above_recheck",
        "probability_move_official_update_below_recheck",
        "probability_move_liquidity_movement_below_recheck",
        "probability_move_specialist_confidence_below_recheck",
        "probability_move_resolution_horizon_unjustified",
        "probability_move_support_score_below_recheck",
    )

    assert watch_row.probability_velocity_per_hour == d("0.080000")
    assert watch_row.evidence_gap_probability == d("0.030000")
    assert watch_row.resolution_horizon_justification_score == d("0.869565")
    assert watch_row.support_score == d("0.686685")
    assert watch_row.gate_status == "watch"
    assert watch_row.reason_codes == (
        "probability_move_velocity_above_watch",
        "probability_move_official_update_below_watch",
        "probability_move_liquidity_movement_below_watch",
        "probability_move_specialist_confidence_below_watch",
        "probability_move_resolution_horizon_watch",
        "probability_move_support_score_below_watch",
    )

    assert clear_row.gate_status == "clear"
    assert clear_row.support_score == d("0.880000")
    assert clear_row.reason_codes == ("probability_move_gate_clear",)
    assert len({row.derived_validation_digest for row in result.rows}) == 3


def test_empty_report_is_readonly_zeroed_and_digest_bound() -> None:
    module = api()
    empty = report()

    assert type(empty) is module.StrategyMarketProbabilityMoveRecheckGateV2Report
    assert empty.market_count == ZERO
    assert empty.clear_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.recheck_required_count == ZERO
    assert empty.max_market_probability_delta == ZERO
    assert empty.max_probability_velocity_per_hour == ZERO
    assert empty.max_evidence_gap_probability == ZERO
    assert empty.min_support_score == ZERO
    assert empty.gate_status == "clear"
    assert empty.recommended_next_step == "continue_report_only_probability_move_recheck"
    assert empty.reason_codes == ("probability_move_gate_empty",)
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in empty.derived_validation_digest)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    for public_value in (config(), snapshot(), empty):
        assert is_dataclass(public_value)
        assert public_value.__dataclass_params__.frozen is True


def test_public_payload_uses_decimal_strings_and_rejects_tampering() -> None:
    module = api()
    result = report(
        snapshot(
            market_slug="payload-market",
            condition_id="condition-payload",
            previous_market_probability=d("0.520000"),
            current_market_probability=d("0.700000"),
            evidence_probability_delta=d("0.050000"),
            official_source_update_score=d("0.300000"),
            liquidity_movement_score=d("0.250000"),
            specialist_confidence_score=d("0.300000"),
            resolution_horizon_hours=d("1000.000000"),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_market_probability_move_recheck_gate_v2_public_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["max_probability_velocity_per_hour"] == "0.180000"
    assert payload["max_evidence_gap_probability"] == "0.130000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-06T11:50:00+00:00"
    assert payload["rows"][0]["support_score"] == "0.239445"
    assert payload["rows"][0]["paper_only"] is True
    assert module.validate_strategy_market_probability_move_recheck_gate_v2_public_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    numeric_payload = {**payload, "market_count": 1}
    with pytest.raises(ValueError, match="Decimal strings|numeric"):
        module.validate_strategy_market_probability_move_recheck_gate_v2_public_payload(
            numeric_payload,
        )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_market_probability_move_recheck_gate_v2_public_payload(
            missing_digest,
        )

    tampered = {**payload, "recheck_required_count": "0.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_market_probability_move_recheck_gate_v2_public_payload(
            tampered,
        )

    tampered_report = replace(result)
    object.__setattr__(tampered_report, "recheck_required_count", d("99.000000"))
    with pytest.raises(ValueError, match="recheck_required_count|derived_validation_digest"):
        module.strategy_market_probability_move_recheck_gate_v2_public_payload(
            tampered_report,
        )


@pytest.mark.parametrize(
    ("key", "value"),
    (
        (unsafe_text("li", "ve", "_enabled"), "not allowed"),
        (unsafe_text("au", "th", "_token"), "not allowed"),
        (unsafe_text("wal", "let", "_address"), "not allowed"),
        (unsafe_text("ord", "er", "_id"), "not allowed"),
        (unsafe_text("net", "work", "_url"), "not allowed"),
        (unsafe_text("data", "base", "_dsn"), "not allowed"),
        (unsafe_text("per", "sist", "_path"), "not allowed"),
        (unsafe_text("sig", "ning", "_key"), "not allowed"),
        (unsafe_text("mu", "tation", "_path"), "not allowed"),
        (unsafe_text("bu", "y", "_flag"), "not allowed"),
        (unsafe_text("sel", "l", "_flag"), "not allowed"),
        (unsafe_text("tra", "de", "_id"), "not allowed"),
        ("operator_note", unsafe_text("configured ", "li", "ve", " surface")),
        ("operator_note", unsafe_text("configured ", "au", "th", " surface")),
        ("operator_note", unsafe_text("configured ", "wal", "let", " surface")),
        ("operator_note", unsafe_text("configured ", "ord", "er", " surface")),
        ("operator_note", unsafe_text("configured ", "net", "work", " surface")),
        ("operator_note", unsafe_text("configured ", "data", "base", " surface")),
        ("operator_note", unsafe_text("configured ", "per", "sist", " surface")),
        ("operator_note", unsafe_text("configured ", "sig", "ning", " surface")),
        ("operator_note", unsafe_text("configured ", "mu", "tation", " surface")),
        ("operator_note", unsafe_text("configured ", "bu", "y", " surface")),
        ("operator_note", unsafe_text("configured ", "sel", "l", " surface")),
        ("operator_note", unsafe_text("configured ", "tra", "de", " surface")),
    ),
)
def test_public_payload_rejects_unsafe_public_keys_and_values(
    key: str,
    value: str,
) -> None:
    module = api()
    payload = module.strategy_market_probability_move_recheck_gate_v2_public_payload(
        report(snapshot(market_slug="unsafe-check", condition_id="condition-unsafe")),
    )

    unsafe_payload = {**payload, key: value}
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_strategy_market_probability_move_recheck_gate_v2_public_payload(
            unsafe_payload,
        )


def test_validation_rejects_bad_types_flags_duplicates_time_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_market_probability_move_recheck_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 6, 11, 50))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 6, 11, 50, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="after generated_at"):
        report(snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate market probability snapshot"):
        report(
            snapshot(market_slug="dup", condition_id="condition-dup"),
            snapshot(market_slug="dup", condition_id="condition-dup"),
        )
    with pytest.raises(ValueError, match="elapsed_minutes"):
        snapshot(elapsed_minutes=d("0.000000"))
    with pytest.raises(ValueError, match="current_market_probability"):
        snapshot(current_market_probability=1)
    with pytest.raises(ValueError, match="previous_market_probability"):
        snapshot(previous_market_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="evidence_probability_delta"):
        snapshot(evidence_probability_delta=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        snapshot(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)

    clear_report = report(snapshot(market_slug="consistency", condition_id="condition-consistency"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(clear_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="clear_count"):
        replace(clear_report, clear_count=d("2.000000"))

    with pytest.raises(FrozenInstanceError):
        clear_report.gate_status = "recheck_required"  # type: ignore[misc]


def test_export_contract_and_static_no_external_surfaces() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_STRATEGY_MARKET_PROBABILITY_MOVE_RECHECK_GATE_V2_CONFIG_VERSION",
        "StrategyMarketProbabilityMoveRecheckGateV2Config",
        "StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount",
        "StrategyMarketProbabilityMoveRecheckGateV2Report",
        "StrategyMarketProbabilityMoveRecheckGateV2Row",
        "StrategyMarketProbabilityMoveRecheckGateV2Snapshot",
        "build_strategy_market_probability_move_recheck_gate_v2_report",
        "strategy_market_probability_move_recheck_gate_v2_public_payload",
        "validate_strategy_market_probability_move_recheck_gate_v2_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for instance in (
        config(),
        snapshot(),
        *report(snapshot()).rows,
        report(snapshot()),
    ):
        for field in fields(instance):
            value = getattr(instance, field.name)
            assert type(value) is not float
            if field.name.endswith(
                (
                    "_count",
                    "_probability",
                    "_delta",
                    "_velocity_per_hour",
                    "_score",
                    "_minutes",
                    "_hours",
                    "_weight",
                ),
            ):
                assert value is None or type(value) is Decimal

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    forbidden_source_fragments = (
        "asyncio",
        "httpx",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "open(",
        ".write(",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
