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
    module_name = "polymarket_alpha_lab.strategy_candidate_tail_risk_digest"
    assert importlib.util.find_spec(module_name) is not None
    return importlib.import_module(module_name)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_TAIL_RISK_DIGEST_CONFIG_VERSION
        ),
        "watch_feature_score": d("0.350000"),
        "block_feature_score": d("0.700000"),
        "watch_tail_risk_score": d("0.400000"),
        "block_tail_risk_score": d("0.700000"),
    }
    values.update(overrides)
    return module.StrategyCandidateTailRiskDigestConfig(**values)


def record(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_reference": "market-alpha",
        "observed_at": OBSERVED_AT,
        "binary_resolution_ambiguity_score": d("0.100000"),
        "liquidity_slippage_tail_score": d("0.120000"),
        "correlated_catalyst_exposure_score": d("0.130000"),
        "late_information_shock_score": d("0.140000"),
        "maximum_loss_concentration_score": d("0.150000"),
        "reason_codes": ("candidate_input",),
    }
    values.update(overrides)
    return module.StrategyCandidateTailRiskRecord(**values)


def report(*records: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_candidate_tail_risk_digest(
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


def test_digest_scores_pass_watch_and_block_tail_features() -> None:
    result = report(
        record(
            candidate_reference="secret-pass-token",
            market_reference="public-pass-market",
            binary_resolution_ambiguity_score=d("0.100000"),
            liquidity_slippage_tail_score=d("0.120000"),
            correlated_catalyst_exposure_score=d("0.130000"),
            late_information_shock_score=d("0.140000"),
            maximum_loss_concentration_score=d("0.150000"),
            reason_codes=("candidate_input", "candidate_input"),
        ),
        record(
            candidate_reference="watch-alpha",
            market_reference="watch-market",
            binary_resolution_ambiguity_score=d("0.360000"),
            liquidity_slippage_tail_score=d("0.450000"),
            correlated_catalyst_exposure_score=d("0.200000"),
            late_information_shock_score=d("0.410000"),
            maximum_loss_concentration_score=d("0.300000"),
        ),
        record(
            candidate_reference="block-alpha",
            market_reference="block-market",
            binary_resolution_ambiguity_score=d("0.800000"),
            liquidity_slippage_tail_score=d("0.900000"),
            correlated_catalyst_exposure_score=d("0.750000"),
            late_information_shock_score=d("0.720000"),
            maximum_loss_concentration_score=d("0.850000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-candidate-tail-risk-digest-v0"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.max_tail_risk_score == d("0.900000")
    assert result.max_binary_resolution_ambiguity_score == d("0.800000")
    assert result.max_liquidity_slippage_tail_score == d("0.900000")
    assert result.max_correlated_catalyst_exposure_score == d("0.750000")
    assert result.max_late_information_shock_score == d("0.720000")
    assert result.max_maximum_loss_concentration_score == d("0.850000")
    assert result.status == "block"
    assert result.reason_codes == (
        "binary_resolution_ambiguity_block",
        "liquidity_slippage_tail_block",
        "correlated_catalyst_exposure_block",
        "late_information_shock_block",
        "maximum_loss_concentration_block",
        "binary_resolution_ambiguity_watch",
        "liquidity_slippage_tail_watch",
        "late_information_shock_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    blocked, watched, passed = result.rows

    assert blocked.tail_risk_score == d("0.900000")
    assert blocked.reason_codes == (
        "binary_resolution_ambiguity_block",
        "candidate_input",
        "correlated_catalyst_exposure_block",
        "late_information_shock_block",
        "liquidity_slippage_tail_block",
        "maximum_loss_concentration_block",
    )
    assert watched.tail_risk_score == d("0.450000")
    assert watched.reason_codes == (
        "binary_resolution_ambiguity_watch",
        "candidate_input",
        "late_information_shock_watch",
        "liquidity_slippage_tail_watch",
    )
    assert passed.tail_risk_score == d("0.150000")
    assert passed.reason_codes == (
        "candidate_input",
        "strategy_candidate_tail_risk_pass",
    )
    assert passed.redacted_candidate_reference.startswith("candidate_ref_")
    assert passed.redacted_market_reference.startswith("market_ref_")


def test_empty_report_is_pass_zeroed_decimal_and_readonly() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.max_tail_risk_score == ZERO
    assert result.max_binary_resolution_ambiguity_score == ZERO
    assert result.max_liquidity_slippage_tail_score == ZERO
    assert result.max_correlated_catalyst_exposure_score == ZERO
    assert result.max_late_information_shock_score == ZERO
    assert result.max_maximum_loss_concentration_score == ZERO
    assert result.status == "pass"
    assert result.reason_codes == ("strategy_candidate_tail_risk_digest_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    populated = report(record())
    for value in (result, *populated.rows, populated):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(("_count", "_score")):
                assert type(item_value) is Decimal


def test_payload_redacts_references_uses_decimal_strings_and_no_public_numbers() -> None:
    module = api()
    result = report(
        record(
            candidate_reference="secret-wallet-token-alpha",
            market_reference="public-market-secret-token",
            binary_resolution_ambiguity_score=d("0.800000"),
            liquidity_slippage_tail_score=d("0.900000"),
            correlated_catalyst_exposure_score=d("0.750000"),
            late_information_shock_score=d("0.720000"),
            maximum_loss_concentration_score=d("0.850000"),
        ),
        generated_at=datetime(2026, 7, 4, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_candidate_tail_risk_digest_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["max_tail_risk_score"] == "0.900000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T11:30:00+00:00"
    assert payload["rows"][0]["tail_risk_score"] == "0.900000"
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


def test_rejects_invalid_inputs_thresholds_datetimes_and_flags() -> None:
    module = api()
    valid_record = record()
    cfg = config()

    with pytest.raises(ValueError, match="records"):
        module.build_strategy_candidate_tail_risk_digest(
            "bad-records",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="StrategyCandidateTailRiskRecord"):
        module.build_strategy_candidate_tail_risk_digest(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_tail_risk_digest(
            [valid_record],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_strategy_candidate_tail_risk_digest(
            [valid_record],
            config=cfg,
            generated_at=datetime(2026, 7, 4, 12, 0),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        record(observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at"):
        report(replace(valid_record, observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(valid_record, valid_record)
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid_record, paper_only=False)
    with pytest.raises(ValueError, match="block_feature_score"):
        config(block_feature_score=d("0.300000"))
    with pytest.raises(ValueError, match="block_tail_risk_score"):
        config(block_tail_risk_score=d("0.300000"))
    with pytest.raises(ValueError, match="report"):
        module.strategy_candidate_tail_risk_digest_payload(object())


def test_dataclasses_are_frozen_exact_and_reject_float_int_or_subclass_values() -> None:
    module = api()
    row = report(record()).rows[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]

    for klass in (
        module.StrategyCandidateTailRiskDigestConfig,
        module.StrategyCandidateTailRiskRecord,
        module.StrategyCandidateTailRiskDigestRow,
        module.StrategyCandidateTailRiskDigestReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="Decimal"):
        record(binary_resolution_ambiguity_score=0.5)
    with pytest.raises(ValueError, match="Decimal"):
        record(binary_resolution_ambiguity_score=1)
    with pytest.raises(ValueError, match="exact Decimal"):
        record(binary_resolution_ambiguity_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="datetime"):
        record(observed_at=_DatetimeSubclass(2026, 7, 4, 11, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report(record()), candidate_count=1)
    with pytest.raises(ValueError, match="redacted_candidate_reference"):
        module.StrategyCandidateTailRiskDigestRow(
            redacted_candidate_reference="candidate_ref_secret-token",
            redacted_market_reference="market_ref_0123456789abcdef",
            observed_at=OBSERVED_AT,
            binary_resolution_ambiguity_score=d("0.100000"),
            liquidity_slippage_tail_score=d("0.120000"),
            correlated_catalyst_exposure_score=d("0.130000"),
            late_information_shock_score=d("0.140000"),
            maximum_loss_concentration_score=d("0.150000"),
            tail_risk_score=d("0.150000"),
            status="pass",
            reason_codes=("strategy_candidate_tail_risk_pass",),
        )


def test_reference_redaction_hides_sensitive_values_from_repr_payload_and_errors() -> None:
    module = api()
    raw_candidate = "secret-wallet-token-candidate"
    raw_market = "public-market-secret-token"
    candidate_record = record(
        candidate_reference=raw_candidate,
        market_reference=raw_market,
    )

    rendered_input = repr(candidate_record).lower()
    assert raw_candidate not in rendered_input
    assert raw_market not in rendered_input
    assert "secret" not in rendered_input
    assert "wallet" not in rendered_input
    assert "token" not in rendered_input

    payload = module.strategy_candidate_tail_risk_digest_payload(report(candidate_record))
    rendered_payload = repr(payload).lower()
    for fragment in ("secret", "wallet", "token", "public-market"):
        assert fragment not in rendered_payload

    with pytest.raises(ValueError) as exc_info:
        record(
            candidate_reference=raw_candidate,
            market_reference=raw_market,
            binary_resolution_ambiguity_score=0.5,
        )
    assert "secret" not in str(exc_info.value).lower()
    assert "wallet" not in str(exc_info.value).lower()
    assert "token" not in str(exc_info.value).lower()


def test_source_has_no_io_db_network_or_live_action_surface() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    banned_import_roots = {
        "asyncio",
        "builtins.open",
        "csv",
        "http",
        "json",
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
    assert not (set(imports) & banned_import_roots)

    lowered = source.lower()
    for term in (
        "db",
        "database",
        "persist",
        "storage",
        "network",
        "live",
        "trade",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
    ):
        assert term not in lowered
