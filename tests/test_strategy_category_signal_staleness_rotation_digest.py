from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_category_signal_staleness_rotation_digest import (
    DEFAULT_STRATEGY_CATEGORY_SIGNAL_STALENESS_ROTATION_DIGEST_CONFIG_VERSION,
    StrategyCategorySignalStalenessRotationCategoryRow,
    StrategyCategorySignalStalenessRotationDigestConfig,
    StrategyCategorySignalStalenessRotationDigestReport,
    StrategyCategorySignalStalenessRotationObservation,
    build_strategy_category_signal_staleness_rotation_digest,
    strategy_category_signal_staleness_rotation_digest_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_category_signal_staleness_rotation_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 3, 17, 0, tzinfo=UTC)


class DateTimeSubclass(datetime):
    pass


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyCategorySignalStalenessRotationDigestConfig:
    values = {
        "config_version": (
            DEFAULT_STRATEGY_CATEGORY_SIGNAL_STALENESS_ROTATION_DIGEST_CONFIG_VERSION
        ),
        "stale_signal_after_seconds": d("3600.000000"),
        "rotate_out_signal_age_seconds": d("7200.000000"),
        "minimum_signal_quality_ratio": d("0.500000"),
        "minimum_rotation_share_delta_ratio": d("0.100000"),
    }
    values.update(overrides)
    return StrategyCategorySignalStalenessRotationDigestConfig(**values)


def observation(
    category_id: str,
    *,
    observed_at: datetime = OBSERVED_AT,
    signal_generated_at: datetime = GENERATED_AT - timedelta(minutes=30),
    signal_quality_ratio: Decimal = d("0.800000"),
    recommended_signal_weight: Decimal = d("50.000000"),
    reason_codes: tuple[str, ...] = ("source_signal_observed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyCategorySignalStalenessRotationObservation:
    return StrategyCategorySignalStalenessRotationObservation(
        category_id=category_id,
        observed_at=observed_at,
        signal_generated_at=signal_generated_at,
        signal_quality_ratio=signal_quality_ratio,
        recommended_signal_weight=recommended_signal_weight,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: StrategyCategorySignalStalenessRotationObservation,
    cfg: StrategyCategorySignalStalenessRotationDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyCategorySignalStalenessRotationDigestReport:
    return build_strategy_category_signal_staleness_rotation_digest(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for key, item in value.items():
            items.append(key)
            items.extend(walk(item))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(walk(item))
        return tuple(items)
    return (value,)


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_weight")
        ):
            assert type(value) is Decimal, field.name


def test_digest_rotates_stale_strategy_category_signals_deterministically() -> None:
    digest = report(
        observation(
            "sports",
            observed_at=OBSERVED_AT - timedelta(minutes=40),
            signal_generated_at=GENERATED_AT - timedelta(minutes=25),
            signal_quality_ratio=d("0.900000"),
            recommended_signal_weight=d("20.000000"),
        ),
        observation(
            "crypto",
            observed_at=OBSERVED_AT - timedelta(minutes=30),
            signal_generated_at=GENERATED_AT - timedelta(minutes=20),
            signal_quality_ratio=d("0.850000"),
            recommended_signal_weight=d("70.000000"),
        ),
        observation(
            "macro",
            observed_at=OBSERVED_AT - timedelta(minutes=20),
            signal_generated_at=GENERATED_AT - timedelta(minutes=45),
            signal_quality_ratio=d("0.600000"),
            recommended_signal_weight=d("30.000000"),
        ),
        observation(
            "sports",
            observed_at=OBSERVED_AT,
            signal_generated_at=GENERATED_AT - timedelta(minutes=130),
            signal_quality_ratio=d("0.350000"),
            recommended_signal_weight=d("10.000000"),
            reason_codes=("manual_signal_review",),
        ),
        observation(
            "crypto",
            observed_at=OBSERVED_AT,
            signal_generated_at=GENERATED_AT - timedelta(minutes=80),
            signal_quality_ratio=d("0.450000"),
            recommended_signal_weight=d("20.000000"),
        ),
        observation(
            "macro",
            observed_at=OBSERVED_AT,
            signal_generated_at=GENERATED_AT - timedelta(minutes=30),
            signal_quality_ratio=d("0.700000"),
            recommended_signal_weight=d("90.000000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert (
        digest.config_version
        == DEFAULT_STRATEGY_CATEGORY_SIGNAL_STALENESS_ROTATION_DIGEST_CONFIG_VERSION
    )
    assert digest.observation_count == d("6")
    assert digest.category_count == d("3")
    assert digest.rotate_out_count == d("1")
    assert digest.watch_count == d("1")
    assert digest.hold_count == d("1")
    assert digest.stale_category_count == d("2")
    assert digest.low_quality_category_count == d("2")
    assert digest.max_signal_age_seconds == d("7800.000000")
    assert digest.average_signal_age_seconds == d("4800.000000")
    assert digest.status == "blocked"
    assert digest.reason_codes == (
        "category_signal_staleness_rotate_out",
        "category_signal_staleness_watch",
        "category_signal_staleness_hold",
        "category_rotation_decrease",
        "category_rotation_increase",
        "stale_signal_age",
        "fresh_signal_age",
        "low_signal_quality",
        "healthy_signal_quality",
        "category_signal_rotation_detected",
        "manual_signal_review",
        "source_signal_observed",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    assert tuple(row.category_id for row in digest.category_rows) == (
        "sports",
        "crypto",
        "macro",
    )
    rotate_out, watched, held = digest.category_rows

    assert rotate_out == StrategyCategorySignalStalenessRotationCategoryRow(
        category_id="sports",
        first_observed_at=OBSERVED_AT - timedelta(minutes=40),
        latest_observed_at=OBSERVED_AT,
        latest_signal_generated_at=GENERATED_AT - timedelta(minutes=130),
        starting_signal_weight=d("20.000000"),
        ending_signal_weight=d("10.000000"),
        signal_weight_delta=d("-10.000000"),
        starting_signal_share_ratio=d("0.166667"),
        ending_signal_share_ratio=d("0.083333"),
        signal_share_delta_ratio=d("-0.083334"),
        latest_signal_age_seconds=d("7800.000000"),
        signal_quality_ratio=d("0.350000"),
        signal_quality_gap_ratio=d("-0.150000"),
        rotation_direction="decrease",
        rotation_status="rotate_out",
        reason_codes=(
            "category_signal_staleness_rotate_out",
            "category_rotation_stable",
            "stale_signal_age",
            "low_signal_quality",
            "manual_signal_review",
            "source_signal_observed",
        ),
    )
    assert watched.rotation_status == "watch"
    assert watched.rotation_direction == "decrease"
    assert watched.latest_signal_age_seconds == d("4800.000000")
    assert watched.signal_quality_gap_ratio == d("-0.050000")
    assert watched.starting_signal_share_ratio == d("0.583333")
    assert watched.ending_signal_share_ratio == d("0.166667")
    assert watched.signal_share_delta_ratio == d("-0.416666")
    assert watched.reason_codes == (
        "category_signal_staleness_watch",
        "category_rotation_decrease",
        "stale_signal_age",
        "low_signal_quality",
        "source_signal_observed",
    )
    assert held.rotation_status == "hold"
    assert held.rotation_direction == "increase"
    assert held.latest_signal_age_seconds == d("1800.000000")
    assert held.signal_quality_gap_ratio == d("0.200000")
    assert held.starting_signal_share_ratio == d("0.250000")
    assert held.ending_signal_share_ratio == d("0.750000")
    assert held.signal_share_delta_ratio == d("0.500000")
    assert held.reason_codes == (
        "category_signal_staleness_hold",
        "category_rotation_increase",
        "fresh_signal_age",
        "healthy_signal_quality",
        "source_signal_observed",
    )


def test_empty_digest_is_report_only_zeroed_decimal_and_json_ready() -> None:
    digest = report()

    assert digest == StrategyCategorySignalStalenessRotationDigestReport(
        generated_at=GENERATED_AT,
        config_version=(
            DEFAULT_STRATEGY_CATEGORY_SIGNAL_STALENESS_ROTATION_DIGEST_CONFIG_VERSION
        ),
        observation_count=d("0"),
        category_count=d("0"),
        rotate_out_count=d("0"),
        watch_count=d("0"),
        hold_count=d("0"),
        stale_category_count=d("0"),
        low_quality_category_count=d("0"),
        max_signal_age_seconds=d("0.000000"),
        average_signal_age_seconds=d("0.000000"),
        status="watch",
        reason_codes=("strategy_category_signal_staleness_rotation_empty",),
        category_rows=(),
    )

    payload = strategy_category_signal_staleness_rotation_digest_payload(digest)
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-03T18:00:00+00:00"
    assert payload["observation_count"] == "0"
    assert payload["max_signal_age_seconds"] == "0.000000"
    assert payload["category_rows"] == []
    assert not any(isinstance(value, float) for value in walk(payload))


def test_payload_uses_decimal_strings_and_utc_aware_datetime_normalization() -> None:
    digest = report(
        observation(
            "macro",
            observed_at=datetime(2026, 7, 3, 10, 30, tzinfo=timezone(timedelta(hours=-7))),
            signal_generated_at=datetime(
                2026,
                7,
                3,
                10,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
            signal_quality_ratio=d("0.650000"),
            recommended_signal_weight=d("12.500000"),
        ),
        generated_at=datetime(2026, 7, 3, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = strategy_category_signal_staleness_rotation_digest_payload(digest)

    assert payload["generated_at"] == "2026-07-03T18:00:00+00:00"
    assert payload["observation_count"] == "1"
    assert payload["max_signal_age_seconds"] == "3600.000000"
    assert payload["category_rows"][0]["latest_observed_at"] == "2026-07-03T17:30:00+00:00"
    assert (
        payload["category_rows"][0]["latest_signal_generated_at"]
        == "2026-07-03T17:00:00+00:00"
    )
    assert payload["category_rows"][0]["ending_signal_weight"] == "12.500000"
    assert payload["category_rows"][0]["paper_only"] is True
    assert payload["category_rows"][0]["report_only"] is True
    assert payload["category_rows"][0]["readonly"] is True
    assert not any(isinstance(value, float) for value in walk(payload))


def test_public_strings_reject_unsafe_or_sensitive_text() -> None:
    with pytest.raises(ValueError, match="public text"):
        observation("wallet_surface")

    with pytest.raises(ValueError, match="public text"):
        observation("crypto", reason_codes=("api_key_leak",))

    with pytest.raises(ValueError, match="public text"):
        config(config_version="strategy-category-secret-token-v0")


def test_public_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    digest = report(observation("crypto"))
    row = digest.category_rows[0]

    with pytest.raises(FrozenInstanceError):
        row.rotation_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="stale_signal_after_seconds must be a Decimal"):
        config(stale_signal_after_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="signal_quality_ratio must be a Decimal"):
        observation("crypto", signal_quality_ratio=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="finite"):
        observation("crypto", recommended_signal_weight=Decimal("NaN"))
    with pytest.raises(ValueError, match="timezone-aware"):
        observation("crypto", signal_generated_at=datetime(2026, 7, 3, 18, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_strategy_category_signal_staleness_rotation_digest(
            (),
            config=config(),
            generated_at=DateTimeSubclass(2026, 7, 3, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(
            "crypto",
            observed_at=DateTimeSubclass(2026, 7, 3, 17, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="recommended_signal_weight must be a Decimal"):
        observation(
            "crypto",
            recommended_signal_weight=DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="signal_generated_at must be <= generated_at"):
        report(
            observation(
                "crypto",
                signal_generated_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="observed_at must be <= generated_at"):
        report(observation("crypto", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate category_id/observed_at"):
        report(
            observation("crypto", observed_at=OBSERVED_AT),
            observation("crypto", observed_at=OBSERVED_AT),
        )
    with pytest.raises(ValueError, match="paper_only"):
        observation("crypto", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="category_count must match category_rows"):
        replace(digest, category_count=d("9"))
    with pytest.raises(ValueError, match="category_rows must contain"):
        replace(digest, category_rows=(object(),))  # type: ignore[arg-type]

    for instance in (config(), observation("decimal-check"), digest, row):
        assert_public_numeric_fields_are_decimal(instance)


def test_payload_requires_report_type_and_hard_flags() -> None:
    digest = report(observation("crypto"))

    with pytest.raises(ValueError, match="report must be"):
        strategy_category_signal_staleness_rotation_digest_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        strategy_category_signal_staleness_rotation_digest_payload(
            replace(digest, readonly=False),
        )


def test_category_rows_reject_tampered_derived_fields() -> None:
    digest = report(
        observation(
            "crypto",
            observed_at=OBSERVED_AT - timedelta(minutes=30),
            signal_generated_at=GENERATED_AT - timedelta(minutes=20),
            signal_quality_ratio=d("0.850000"),
            recommended_signal_weight=d("70.000000"),
        ),
        observation(
            "crypto",
            observed_at=OBSERVED_AT,
            signal_generated_at=GENERATED_AT - timedelta(minutes=80),
            signal_quality_ratio=d("0.450000"),
            recommended_signal_weight=d("20.000000"),
        ),
        observation(
            "macro",
            observed_at=OBSERVED_AT - timedelta(minutes=30),
            signal_generated_at=GENERATED_AT - timedelta(minutes=20),
            signal_quality_ratio=d("0.850000"),
            recommended_signal_weight=d("30.000000"),
        ),
        observation(
            "macro",
            observed_at=OBSERVED_AT,
            signal_generated_at=GENERATED_AT - timedelta(minutes=20),
            signal_quality_ratio=d("0.850000"),
            recommended_signal_weight=d("80.000000"),
        ),
    )
    row = digest.category_rows[0]

    with pytest.raises(ValueError, match="signal_share_delta_ratio"):
        replace(row, signal_share_delta_ratio=d("0.000000"))
    with pytest.raises(ValueError, match="rotation_direction"):
        replace(row, rotation_direction="hold")
    with pytest.raises(ValueError, match="rotation_status"):
        replace(row, rotation_status="hold")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("source_signal_observed",))


def test_digest_report_rejects_tampered_derived_fields() -> None:
    digest = report(
        observation(
            "sports",
            observed_at=OBSERVED_AT - timedelta(minutes=40),
            signal_generated_at=GENERATED_AT - timedelta(minutes=130),
            signal_quality_ratio=d("0.350000"),
            recommended_signal_weight=d("10.000000"),
        ),
        observation(
            "macro",
            observed_at=OBSERVED_AT,
            signal_generated_at=GENERATED_AT - timedelta(minutes=30),
            signal_quality_ratio=d("0.700000"),
            recommended_signal_weight=d("90.000000"),
        ),
    )

    with pytest.raises(ValueError, match="stale_category_count"):
        replace(digest, stale_category_count=d("9"))
    with pytest.raises(ValueError, match="low_quality_category_count"):
        replace(digest, low_quality_category_count=d("9"))
    with pytest.raises(ValueError, match="max_signal_age_seconds"):
        replace(digest, max_signal_age_seconds=d("1.000000"))
    with pytest.raises(ValueError, match="average_signal_age_seconds"):
        replace(digest, average_signal_age_seconds=d("1.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="pass")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(digest, reason_codes=("healthy_signal_quality",))


def test_payload_rejects_unsafe_public_payload_dicts_and_missing_flags() -> None:
    digest = report(observation("crypto"))
    payload = strategy_category_signal_staleness_rotation_digest_payload(digest)

    with pytest.raises(ValueError, match="readonly"):
        strategy_category_signal_staleness_rotation_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        strategy_category_signal_staleness_rotation_digest_payload(
            {
                **payload,
                "unsafe_public_value": "wallet_surface",
            },
        )
    with pytest.raises(ValueError, match="paper_only"):
        strategy_category_signal_staleness_rotation_digest_payload(
            {
                **payload,
                "category_rows": [
                    {
                        **payload["category_rows"][0],
                        "paper_only": False,
                    },
                ],
            },
        )


def test_module_scope_has_no_io_durable_store_network_auth_or_trading_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    call_names: set[str] = set()
    attr_names: set[str] = set()
    forbidden_identifier_fragments = (
        "account",
        "auth",
        "broker",
        "clob",
        "client",
        "database",
        "db",
        "durable",
        "http",
        "network",
        "order",
        "private_key",
        "socket",
        "sqlite",
        "store",
        "trade",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attr_names.add(node.attr)
        elif isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in forbidden_identifier_fragments)

    forbidden_imports = {
        "asyncio",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "cancel",
        "connect",
        "create_order",
        "execute",
        "executemany",
        "open",
        "place_order",
        "request",
        "send",
        "sign",
        "submit",
        "urlopen",
        "write",
    }

    assert imported_names.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert attr_names.isdisjoint(forbidden_calls)


def test_public_api_exports_digest_contract() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.strategy_category_signal_staleness_rotation_digest",
    )

    assert module.__all__ == (
        "DEFAULT_STRATEGY_CATEGORY_SIGNAL_STALENESS_ROTATION_DIGEST_CONFIG_VERSION",
        "StrategyCategorySignalStalenessRotationDigestConfig",
        "StrategyCategorySignalStalenessRotationObservation",
        "StrategyCategorySignalStalenessRotationCategoryRow",
        "StrategyCategorySignalStalenessRotationDigestReport",
        "build_strategy_category_signal_staleness_rotation_digest",
        "strategy_category_signal_staleness_rotation_digest_payload",
    )
