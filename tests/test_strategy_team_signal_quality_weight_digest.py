from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_signal_quality_weight_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=timezone(timedelta(hours=2)))
OBSERVED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
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
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_signal_quality_weight_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-team-signal-quality-weight-digest-test-v0",
        "min_pass_weighted_score": d("0.400000"),
        "min_watch_weighted_score": d("0.200000"),
        "min_calibration_quality": d("0.600000"),
        "min_source_reliability": d("0.600000"),
        "max_evidence_age_seconds": d("86400.000000"),
        "max_disagreement_rate": d("0.300000"),
        "min_cost_aware_edge": d("0.020000"),
        "max_drawdown_pressure": d("0.700000"),
    }
    values.update(overrides)
    return module.StrategyTeamSignalQualityWeightDigestConfig(**values)


def signal(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_team",
        "signal_id": "signal_macro",
        "team_reference": "macro-public",
        "observed_at": OBSERVED_AT,
        "calibration_quality": d("0.900000"),
        "source_reliability": d("0.800000"),
        "evidence_age_seconds": d("3600.000000"),
        "disagreement_rate": d("0.100000"),
        "cost_aware_edge": d("0.120000"),
        "drawdown_pressure": d("0.200000"),
        "raw_signal_score": d("0.750000"),
        "reason_codes": ("specialist_signal_quality_input",),
    }
    values.update(overrides)
    return module.StrategyTeamSignalQualityWeightSignal(**values)


def report(*, signals=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_team_signal_quality_weight_digest(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_digest_weights_specialist_signals_with_stable_pass_watch_block_reasons() -> None:
    result = report(
        signals=(
            signal(
                team_id="macro_team",
                signal_id="signal_macro",
                team_reference="macro-public",
                calibration_quality=d("0.900000"),
                source_reliability=d("0.800000"),
                evidence_age_seconds=d("3600.000000"),
                disagreement_rate=d("0.100000"),
                cost_aware_edge=d("0.120000"),
                drawdown_pressure=d("0.200000"),
                raw_signal_score=d("0.750000"),
            ),
            signal(
                team_id="crypto_team",
                signal_id="signal_crypto",
                team_reference="secret-wallet-token-team",
                calibration_quality=d("0.650000"),
                source_reliability=d("0.600000"),
                evidence_age_seconds=d("43200.000000"),
                disagreement_rate=d("0.250000"),
                cost_aware_edge=d("0.030000"),
                drawdown_pressure=d("0.500000"),
                raw_signal_score=d("0.600000"),
            ),
            signal(
                team_id="sports_team",
                signal_id="signal_sports",
                team_reference="sports-public",
                calibration_quality=d("0.450000"),
                source_reliability=d("0.400000"),
                evidence_age_seconds=d("172800.000000"),
                disagreement_rate=d("0.600000"),
                cost_aware_edge=d("-0.010000"),
                drawdown_pressure=d("0.850000"),
                raw_signal_score=d("0.500000"),
            ),
        ),
    )

    assert result.generated_at == datetime(2026, 7, 3, 14, 0, tzinfo=UTC)
    assert result.config_version == "strategy-team-signal-quality-weight-digest-test-v0"
    assert result.signal_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.total_quality_weight == d("1.796250")
    assert result.average_weighted_signal_score == d("0.393354")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "signal_quality_weight_pass",
        "signal_quality_weight_watch",
        "signal_quality_weight_block",
        "calibration_quality_low",
        "source_reliability_low",
        "evidence_stale",
        "disagreement_rate_high",
        "cost_aware_edge_nonpositive",
        "drawdown_pressure_high",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.team_id for row in result.rows) == (
        "macro_team",
        "crypto_team",
        "sports_team",
    )
    assert tuple(row.signal_id for row in result.rows) == (
        "signal_macro",
        "signal_crypto",
        "signal_sports",
    )
    assert tuple(row.status for row in result.rows) == ("pass", "watch", "block")

    passed, watched, blocked = result.rows
    assert passed.freshness_quality == d("0.958333")
    assert passed.quality_weight == d("0.888750")
    assert passed.weighted_signal_score == d("0.666562")
    assert passed.reason_codes == (
        "specialist_signal_quality_input",
        "signal_quality_weight_pass",
        "calibration_quality_strong",
        "source_reliability_strong",
        "evidence_fresh",
        "disagreement_contained",
        "cost_aware_edge_positive",
        "drawdown_pressure_contained",
    )

    assert watched.redacted_team_reference.startswith("team_ref_")
    assert "secret" not in watched.redacted_team_reference
    assert "wallet" not in watched.redacted_team_reference
    assert "token" not in watched.redacted_team_reference
    assert watched.freshness_quality == d("0.500000")
    assert watched.quality_weight == d("0.597500")
    assert watched.weighted_signal_score == d("0.358500")
    assert watched.reason_codes == (
        "specialist_signal_quality_input",
        "signal_quality_weight_watch",
        "evidence_fresh",
        "disagreement_contained",
        "cost_aware_edge_positive",
        "drawdown_pressure_contained",
    )

    assert blocked.freshness_quality == ZERO
    assert blocked.quality_weight == d("0.310000")
    assert blocked.weighted_signal_score == d("0.155000")
    assert blocked.reason_codes == (
        "specialist_signal_quality_input",
        "signal_quality_weight_block",
        "calibration_quality_low",
        "source_reliability_low",
        "evidence_stale",
        "disagreement_rate_high",
        "cost_aware_edge_nonpositive",
        "drawdown_pressure_high",
    )


def test_empty_digest_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.signal_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.total_quality_weight == ZERO
    assert empty.average_weighted_signal_score == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("strategy_team_signal_quality_weight_digest_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(signals=(signal(),))
    for value in (empty, populated, *populated.rows):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_quality",
                    "_reliability",
                    "_seconds",
                    "_rate",
                    "_edge",
                    "_pressure",
                    "_weight",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_redacts_references_uses_decimal_strings_and_no_floats() -> None:
    module = api()
    result = report(
        signals=(
            signal(
                team_id="crypto_team",
                signal_id="signal_crypto",
                team_reference="secret-wallet-token-team",
                calibration_quality=d("0.650000"),
                source_reliability=d("0.600000"),
                evidence_age_seconds=d("43200.000000"),
                disagreement_rate=d("0.250000"),
                cost_aware_edge=d("0.030000"),
                drawdown_pressure=d("0.500000"),
                raw_signal_score=d("0.600000"),
            ),
        ),
        generated_at=datetime(2026, 7, 3, 7, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_team_signal_quality_weight_digest_payload(result)
    rendered = repr(payload).lower()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T14:00:00+00:00"
    assert payload["signal_count"] == "1"
    assert payload["total_quality_weight"] == "0.597500"
    assert payload["average_weighted_signal_score"] == "0.358500"
    assert payload["rows"][0]["redacted_team_reference"].startswith("team_ref_")
    assert payload["rows"][0]["observed_at"] == "2026-07-03T12:00:00+00:00"
    assert '"0.358500"' in encoded
    assert "secret-wallet" not in rendered
    assert "wallet" not in rendered
    assert "token" not in rendered
    assert_no_float_values(payload)


def test_validation_rejects_bad_types_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_team_signal_quality_weight_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="calibration_quality must be a Decimal"):
        signal(calibration_quality=0.8)

    with pytest.raises(ValueError, match="evidence_age_seconds must be finite"):
        signal(evidence_age_seconds=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 3, 14, 0))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 14, 0, tzinfo=_NoneOffsetTimezone()))

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="cost_aware_edge must be a Decimal"):
        signal(cost_aware_edge=_DecimalSubclass("0.050000"))

    with pytest.raises(ValueError, match="disagreement_rate must be a probability Decimal"):
        signal(disagreement_rate=d("1.000001"))

    with pytest.raises(ValueError, match="duplicate signal_id"):
        report(
            signals=(
                signal(signal_id="signal_same", team_id="macro_team"),
                signal(signal_id="signal_same", team_id="crypto_team"),
            ),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyTeamSignalQualityWeightDigestConfig(paper_only=False)

    row = report(signals=(signal(),)).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_public_strings_reject_unsafe_phase1_surface_values() -> None:
    with pytest.raises(ValueError, match="config_version has unsafe value"):
        config(config_version="wallet-config")

    for field_name, override in (
        ("team_id", {"team_id": "wallet_team"}),
        ("signal_id", {"signal_id": "auth_signal"}),
        ("reason_codes", {"reason_codes": ("order_submission",)}),
    ):
        with pytest.raises(ValueError, match=f"{field_name} has unsafe value"):
            signal(**override)


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report(signals=(signal(),))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_team_signal_quality_weight_digest_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_team_signal_quality_weight_digest_payload(
            replace(result, report_only=False),
        )


def test_module_scope_has_no_live_trading_persistence_network_or_sensitive_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "live_trading",
        "live trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "private_key",
        "secret",
        "token",
        "password",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
        "trade",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
