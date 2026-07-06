from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_source_reliability_weighting_v3.py"
)
GENERATED_AT = datetime(2026, 7, 6, 18, 0, tzinfo=timezone(timedelta(hours=2)))
OBSERVED_AT = datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_source_reliability_weighting_v3",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    weighting = api()
    values = {
        "config_version": "strategy-source-reliability-weighting-v3-test",
        "min_pass_source_weight": d("0.700000"),
        "min_watch_source_weight": d("0.450000"),
        "min_historical_accuracy": d("0.600000"),
        "min_directness": d("0.500000"),
        "max_source_age_seconds": d("86400.000000"),
        "max_conflict_rate": d("0.250000"),
        "official_override_floor": d("0.850000"),
    }
    values.update(overrides)
    return weighting.StrategySourceReliabilityWeightingV3Config(**values)


def source(**overrides: object):
    weighting = api()
    values = {
        "source_id": "source_primary",
        "source_tier": "primary",
        "observed_at": OBSERVED_AT,
        "historical_accuracy": d("0.900000"),
        "source_age_seconds": d("3600.000000"),
        "directness": d("0.800000"),
        "conflict_rate": d("0.050000"),
        "official_override": False,
        "reason_codes": ("historical_audit",),
    }
    values.update(overrides)
    return weighting.StrategySourceReliabilityWeightingV3Source(**values)


def report(*, sources=(), cfg=None, generated_at: datetime = GENERATED_AT):
    weighting = api()
    return weighting.build_strategy_source_reliability_weighting_v3(
        sources,
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


def test_weighting_v3_scores_sources_from_tier_accuracy_recency_directness_conflicts_and_official_override() -> None:
    weighted_report = report(
        sources=(
            source(),
            source(
                source_id="source_secondary",
                source_tier="secondary",
                historical_accuracy=d("0.680000"),
                source_age_seconds=d("43200.000000"),
                directness=d("0.500000"),
                conflict_rate=d("0.200000"),
                reason_codes=("public_model",),
            ),
            source(
                source_id="source_tertiary",
                source_tier="tertiary",
                historical_accuracy=d("0.400000"),
                source_age_seconds=d("172800.000000"),
                directness=d("0.300000"),
                conflict_rate=d("0.500000"),
                reason_codes=("forum_signal",),
            ),
            source(
                source_id="source_official",
                source_tier="official",
                historical_accuracy=d("0.450000"),
                source_age_seconds=d("172800.000000"),
                directness=d("0.400000"),
                conflict_rate=d("0.600000"),
                official_override=True,
                reason_codes=("official_feed",),
            ),
        ),
    )

    assert is_dataclass(weighted_report)
    assert weighted_report.generated_at == datetime(2026, 7, 6, 16, 0, tzinfo=UTC)
    assert weighted_report.config_version == "strategy-source-reliability-weighting-v3-test"
    assert weighted_report.source_count == d("4")
    assert weighted_report.pass_count == d("2")
    assert weighted_report.watch_count == d("1")
    assert weighted_report.block_count == d("1")
    assert weighted_report.average_source_weight == d("0.673812")
    assert weighted_report.reliability_status == "blocked"
    assert weighted_report.reason_codes == (
        "source_weight_pass",
        "source_weight_watch",
        "source_weight_block",
        "source_official_override",
        "historical_accuracy_low",
        "source_stale",
        "directness_low",
        "source_conflict_rate_high",
    )
    assert weighted_report.paper_only is True
    assert weighted_report.report_only is True
    assert weighted_report.readonly is True

    assert tuple(row.source_id for row in weighted_report.rows) == (
        "source_primary",
        "source_official",
        "source_secondary",
        "source_tertiary",
    )
    assert tuple(row.reliability_status for row in weighted_report.rows) == (
        "pass",
        "pass",
        "watch",
        "block",
    )

    primary, official, secondary, tertiary = weighted_report.rows
    assert primary.tier_weight == d("0.850000")
    assert primary.recency_weight == d("0.958333")
    assert primary.source_weight == d("0.881250")
    assert primary.reason_codes == (
        "historical_audit",
        "source_weight_pass",
        "source_tier_primary",
        "historical_accuracy_strong",
        "source_recent",
        "direct_source",
        "source_conflict_rate_contained",
    )

    assert official.tier_weight == d("1.000000")
    assert official.recency_weight == ZERO
    assert official.source_weight == d("0.850000")
    assert official.reason_codes == (
        "official_feed",
        "source_weight_pass",
        "source_official_override",
        "source_tier_official",
        "historical_accuracy_low",
        "source_stale",
        "directness_low",
        "source_conflict_rate_high",
    )

    assert secondary.tier_weight == d("0.650000")
    assert secondary.recency_weight == d("0.500000")
    assert secondary.source_weight == d("0.621500")
    assert secondary.reason_codes == (
        "public_model",
        "source_weight_watch",
        "source_tier_secondary",
        "source_recency_decay",
        "source_conflict_rate_contained",
    )

    assert tertiary.tier_weight == d("0.450000")
    assert tertiary.recency_weight == ZERO
    assert tertiary.source_weight == d("0.342500")
    assert tertiary.reason_codes == (
        "forum_signal",
        "source_weight_block",
        "source_tier_tertiary",
        "historical_accuracy_low",
        "source_stale",
        "directness_low",
        "source_conflict_rate_high",
    )


def test_empty_weighting_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.source_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.average_source_weight == ZERO
    assert empty.reliability_status == "watch"
    assert empty.reason_codes == ("strategy_source_reliability_weighting_v3_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(sources=(source(),))
    for value in (empty, populated, *populated.rows):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(("_count", "_rate", "_weight", "_accuracy", "_seconds")):
                assert type(item_value) is Decimal


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    weighting = api()
    numeric_fields = {
        "min_pass_source_weight",
        "min_watch_source_weight",
        "min_historical_accuracy",
        "min_directness",
        "max_source_age_seconds",
        "max_conflict_rate",
        "official_override_floor",
        "historical_accuracy",
        "source_age_seconds",
        "directness",
        "conflict_rate",
        "tier_weight",
        "recency_weight",
        "source_weight",
        "source_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_source_weight",
    }

    for cls in (
        weighting.StrategySourceReliabilityWeightingV3Config,
        weighting.StrategySourceReliabilityWeightingV3Source,
        weighting.StrategySourceReliabilityWeightingV3Row,
        weighting.StrategySourceReliabilityWeightingV3Report,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal

    with pytest.raises(ValueError, match="source_weight must be a Decimal"):
        weighting.StrategySourceReliabilityWeightingV3Row(
            source_id="source_bad",
            source_tier="primary",
            observed_at=OBSERVED_AT,
            historical_accuracy=d("0.900000"),
            source_age_seconds=d("3600.000000"),
            directness=d("0.800000"),
            conflict_rate=d("0.050000"),
            official_override=False,
            tier_weight=d("0.850000"),
            recency_weight=d("0.958333"),
            source_weight=None,
            reliability_status="pass",
            reason_codes=("source_weight_pass",),
        )


def test_payload_uses_decimal_strings_utc_datetimes_and_no_floats() -> None:
    weighting = api()
    weighted_report = report(
        sources=(
            source(
                observed_at=datetime(2026, 7, 6, 3, 0, tzinfo=timezone(timedelta(hours=-7))),
            ),
        ),
    )

    payload = weighting.strategy_source_reliability_weighting_v3_payload(weighted_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T16:00:00+00:00"
    assert payload["source_count"] == "1"
    assert payload["average_source_weight"] == "0.881250"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T10:00:00+00:00"
    assert payload["rows"][0]["source_weight"] == "0.881250"
    assert payload["rows"][0]["official_override"] is False
    assert '"0.881250"' in encoded
    assert_no_float_values(payload)


def test_validation_rejects_bad_types_duplicates_naive_time_and_flags() -> None:
    weighting = api()

    with pytest.raises(ValueError, match="config"):
        weighting.build_strategy_source_reliability_weighting_v3(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="historical_accuracy must be a Decimal"):
        source(historical_accuracy=0.9)

    with pytest.raises(ValueError, match="historical_accuracy must be a Decimal"):
        source(historical_accuracy=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="source_age_seconds must be finite"):
        source(source_age_seconds=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 6, 16, 0))

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        source(observed_at=_DatetimeSubclass(2026, 7, 6, 10, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="source_tier"):
        source(source_tier="social")

    with pytest.raises(ValueError, match="duplicate source_id"):
        report(sources=(source(), source()))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(source(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        config(readonly=False)

    with pytest.raises(FrozenInstanceError):
        row = source()
        row.source_id = "other"  # type: ignore[misc]


def test_public_strings_reject_secret_like_values_before_payload_leakage() -> None:
    with pytest.raises(ValueError, match="must not contain sensitive material"):
        config(config_version="strategy-source-password-secret")

    with pytest.raises(ValueError, match="must not contain sensitive material"):
        source(source_id="postgresql://user:secret@db.example.local/postgres")

    with pytest.raises(ValueError, match="must not contain sensitive material"):
        source(reason_codes=("api_key_secret",))


def test_module_scope_has_no_network_database_ordering_or_mutation_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "durable",
        "store",
        "open(",
        "requests",
        "http",
        "socket",
        "fast",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
