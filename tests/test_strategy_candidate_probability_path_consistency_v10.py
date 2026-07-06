from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 4, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    module_name = (
        "polymarket_alpha_lab.strategy_candidate_probability_path_consistency_v10"
    )
    assert importlib.util.find_spec(module_name) is not None
    return importlib.import_module(module_name)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_PROBABILITY_PATH_CONSISTENCY_CONFIG_VERSION
        ),
        "watch_move_magnitude": d("0.120000"),
        "block_move_magnitude": d("0.250000"),
        "watch_reversal_count": d("2"),
        "block_reversal_count": d("4"),
        "watch_evidence_age_hours": d("24"),
        "block_evidence_age_hours": d("72"),
        "watch_liquidity_support_score": d("0.550000"),
        "block_liquidity_support_score": d("0.300000"),
        "watch_source_alignment_score": d("0.600000"),
        "block_source_alignment_score": d("0.350000"),
        "watch_path_consistency_score": d("0.650000"),
        "block_path_consistency_score": d("0.450000"),
        "move_magnitude_weight": d("0.250000"),
        "reversal_weight": d("0.200000"),
        "evidence_freshness_weight": d("0.200000"),
        "liquidity_support_weight": d("0.150000"),
        "source_alignment_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.StrategyCandidateProbabilityPathConsistencyConfig(**values)


def record(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_reference": "market-alpha",
        "observed_at": OBSERVED_AT,
        "start_probability": d("0.400000"),
        "current_probability": d("0.450000"),
        "largest_single_move": d("0.050000"),
        "reversal_count": d("0"),
        "evidence_age_hours": d("2"),
        "liquidity_support_score": d("0.900000"),
        "source_alignment_score": d("0.950000"),
        "reason_codes": ("candidate_input",),
    }
    values.update(overrides)
    return module.StrategyCandidateProbabilityPathConsistencyRecord(**values)


def report(*records: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_candidate_probability_path_consistency_report(
        records,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_scores_pass_watch_and_block_probability_path_consistency() -> None:
    result = report(
        record(
            candidate_reference="secret-pass-token",
            market_reference="public-pass-market",
            start_probability=d("0.400000"),
            current_probability=d("0.450000"),
            largest_single_move=d("0.050000"),
            reversal_count=d("0"),
            evidence_age_hours=d("2"),
            liquidity_support_score=d("0.900000"),
            source_alignment_score=d("0.950000"),
            reason_codes=("candidate_input", "candidate_input"),
        ),
        record(
            candidate_reference="watch-alpha",
            market_reference="watch-market",
            start_probability=d("0.500000"),
            current_probability=d("0.630000"),
            largest_single_move=d("0.180000"),
            reversal_count=d("2"),
            evidence_age_hours=d("36"),
            liquidity_support_score=d("0.500000"),
            source_alignment_score=d("0.700000"),
        ),
        record(
            candidate_reference="block-alpha",
            market_reference="block-market",
            start_probability=d("0.200000"),
            current_probability=d("0.550000"),
            largest_single_move=d("0.350000"),
            reversal_count=d("5"),
            evidence_age_hours=d("100"),
            liquidity_support_score=d("0.200000"),
            source_alignment_score=d("0.300000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert (
        result.config_version
        == "strategy-candidate-probability-path-consistency-v10"
    )
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.min_path_consistency_score == d("0.090000")
    assert result.max_move_magnitude == d("0.350000")
    assert result.max_reversal_count == d("5")
    assert result.max_evidence_age_hours == d("100")
    assert result.min_liquidity_support_score == d("0.200000")
    assert result.min_source_alignment_score == d("0.300000")
    assert result.status == "block"
    assert result.reason_codes == (
        "move_magnitude_block",
        "reversal_count_block",
        "evidence_freshness_block",
        "liquidity_support_block",
        "source_alignment_block",
        "path_consistency_score_block",
        "move_magnitude_watch",
        "reversal_count_watch",
        "evidence_freshness_watch",
        "liquidity_support_watch",
        "path_consistency_score_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    blocked, watched, passed = result.rows

    assert blocked.move_magnitude == d("0.350000")
    assert blocked.path_consistency_score == d("0.090000")
    assert blocked.reason_codes == (
        "candidate_input",
        "evidence_freshness_block",
        "liquidity_support_block",
        "move_magnitude_block",
        "path_consistency_score_block",
        "reversal_count_block",
        "source_alignment_block",
    )
    assert watched.move_magnitude == d("0.180000")
    assert watched.path_consistency_score == d("0.485000")
    assert watched.reason_codes == (
        "candidate_input",
        "evidence_freshness_watch",
        "liquidity_support_watch",
        "move_magnitude_watch",
        "path_consistency_score_watch",
        "reversal_count_watch",
    )
    assert passed.path_consistency_score == d("0.919444")
    assert passed.reason_codes == (
        "candidate_input",
        "strategy_candidate_probability_path_consistency_pass",
    )
    assert passed.redacted_candidate_reference.startswith("candidate_ref_")
    assert passed.redacted_market_reference.startswith("market_ref_")


def test_empty_report_is_pass_zeroed_decimal_and_frozen_readonly() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.min_path_consistency_score == d("0")
    assert result.max_move_magnitude == ZERO
    assert result.max_reversal_count == d("0")
    assert result.max_evidence_age_hours == d("0")
    assert result.min_liquidity_support_score == ZERO
    assert result.min_source_alignment_score == ZERO
    assert result.status == "pass"
    assert result.reason_codes == (
        "strategy_candidate_probability_path_consistency_empty",
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    populated = report(record())
    for value in (result, *populated.rows, populated):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(("_count", "_score", "_magnitude", "_hours")):
                assert type(item_value) is Decimal


def test_payload_redacts_references_uses_decimal_strings_and_no_public_numbers() -> None:
    module = api()
    result = report(
        record(
            candidate_reference="secret-wallet-token-alpha",
            market_reference="public-market-secret-token",
            start_probability=d("0.200000"),
            current_probability=d("0.550000"),
            largest_single_move=d("0.350000"),
            reversal_count=d("5"),
            evidence_age_hours=d("100"),
            liquidity_support_score=d("0.200000"),
            source_alignment_score=d("0.300000"),
        ),
        generated_at=datetime(2026, 7, 4, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_candidate_probability_path_consistency_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["min_path_consistency_score"] == "0.090000"
    assert payload["report_integrity_digest"] == result.report_integrity_digest
    assert len(payload["report_integrity_digest"]) == 64
    assert payload["rows"][0]["observed_at"] == "2026-07-04T11:30:00+00:00"
    assert payload["rows"][0]["path_consistency_score"] == "0.090000"
    assert payload["rows"][0]["result_integrity_digest"] == (
        result.rows[0].result_integrity_digest
    )
    assert len(payload["rows"][0]["result_integrity_digest"]) == 64
    assert payload["rows"][0]["redacted_candidate_reference"].startswith(
        "candidate_ref_",
    )
    assert payload["rows"][0]["redacted_market_reference"].startswith("market_ref_")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    for forbidden in ("secret", "wallet", "token", "public-market"):
        assert forbidden not in rendered
        assert forbidden not in repr(result).lower()
    assert_no_int_or_float_values(payload)


def test_tamper_evident_row_and_report_validation_recomputes_derived_fields() -> None:
    result = report(record())
    row = result.rows[0]

    with pytest.raises(ValueError, match="move_magnitude must match probability path"):
        replace(row, move_magnitude=d("0.060000"))
    with pytest.raises(ValueError, match="result_integrity_digest must match row"):
        replace(row, path_consistency_score=d("0.100000"))
    with pytest.raises(ValueError, match="result_integrity_digest must match row"):
        replace(row, result_integrity_digest="0" * 64)
    with pytest.raises(ValueError, match="candidate_count must match rows"):
        replace(result, candidate_count=d("2"))
    with pytest.raises(ValueError, match="report_integrity_digest must match report"):
        replace(result, report_integrity_digest="0" * 64)


def test_public_payload_rejects_unsafe_surface_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    module = api()
    result = report(record())

    def unsafe_json_ready_no_floats(value: object) -> dict[str, object]:
        assert value is result
        return {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "wallet_balance": "1.000000",
        }

    monkeypatch.setattr(module, "json_ready_no_floats", unsafe_json_ready_no_floats)
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_candidate_probability_path_consistency_payload(result)


def test_rejects_invalid_inputs_thresholds_datetimes_weights_and_flags() -> None:
    module = api()
    valid_record = record()
    cfg = config()

    with pytest.raises(ValueError, match="records"):
        module.build_strategy_candidate_probability_path_consistency_report(
            "bad-records",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="records"):
        module.build_strategy_candidate_probability_path_consistency_report(
            [valid_record, valid_record],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="Decimal"):
        record(start_probability=0.5)
    with pytest.raises(ValueError, match="exact Decimal"):
        record(current_probability=_DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="timezone-aware"):
        record(observed_at=datetime(2026, 7, 4, 11, 30))
    with pytest.raises(ValueError, match="timezone-aware"):
        record(observed_at=_DatetimeSubclass(2026, 7, 4, 11, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        record(observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at"):
        report(record(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="block_move_magnitude"):
        config(watch_move_magnitude=d("0.300000"), block_move_magnitude=d("0.250000"))
    with pytest.raises(ValueError, match="weight"):
        config(source_alignment_weight=d("0.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_candidate_probability_path_consistency_payload(
            replace(report(valid_record), readonly=False),
        )


def test_module_stays_pure_readonly_and_unwired() -> None:
    module = api()
    source_path = Path(module.__file__)
    assert source_path.name == "strategy_candidate_probability_path_consistency_v10.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_imports = {
        "http.client",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "create_order",
        "delete",
        "execute",
        "get",
        "open",
        "patch",
        "place_order",
        "post",
        "put",
        "request",
        "run",
        "send",
        "write",
        "write_text",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name for alias in node.names}
            assert imported.isdisjoint(forbidden_imports)
        if isinstance(node, ast.ImportFrom):
            assert node.module not in forbidden_imports
            assert not (node.module or "").startswith(("urllib", "http"))
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if is_dataclass(exported):
            assert getattr(exported, "__dataclass_params__").frozen is True
