from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_forecast_revision_pressure_score_v2"
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
PRIOR_AT = datetime(2026, 7, 4, 8, 0, tzinfo=UTC)
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


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_FORECAST_REVISION_PRESSURE_SCORE_V2_CONFIG_VERSION
        ),
        "sharp_revision_delta": d("0.100000"),
        "stale_after_hours": d("24.000000"),
        "stale_full_penalty_hours": d("48.000000"),
        "revision_magnitude_weight": d("0.700000"),
        "stale_penalty_weight": d("0.200000"),
        "sharp_revision_boost_weight": d("0.200000"),
        "blocked_pressure_score": d("0.750000"),
        "watch_pressure_score": d("0.400000"),
    }
    values.update(overrides)
    return module.StrategyForecastRevisionPressureScoreV2Config(**values)


def revision(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": "fomc-cut-july",
        "forecast_observed_at": OBSERVED_AT,
        "prior_forecast_observed_at": PRIOR_AT,
        "prior_forecast": d("0.420000"),
        "current_forecast": d("0.500000"),
        "forecast_reference": "plain-ticket",
    }
    values.update(overrides)
    return module.StrategyForecastRevisionPressureObservation(**values)


def pressure_report(
    *rows: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_forecast_revision_pressure_score_v2(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not int
        assert type(value) is not float
        if isinstance(value, Decimal):
            assert type(value) is Decimal
        elif isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_public_numeric_fields_are_decimal(item)


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_forecast_revision_pressure_scores_and_ranks_candidates() -> None:
    report = pressure_report(
        revision(
            candidate_id="rates-stale-sharp",
            forecast_observed_at=GENERATED_AT - timedelta(hours=60),
            prior_forecast_observed_at=GENERATED_AT - timedelta(hours=84),
            prior_forecast=d("0.400000"),
            current_forecast=d("0.580000"),
        ),
        revision(
            candidate_id="sports-moderate",
            forecast_observed_at=GENERATED_AT - timedelta(hours=5),
            prior_forecast_observed_at=GENERATED_AT - timedelta(hours=9),
            prior_forecast=d("0.320000"),
            current_forecast=d("0.400000"),
        ),
        revision(
            candidate_id="weather-stale-flat",
            forecast_observed_at=GENERATED_AT - timedelta(hours=72),
            prior_forecast_observed_at=GENERATED_AT - timedelta(hours=96),
            prior_forecast=d("0.510000"),
            current_forecast=d("0.510000"),
        ),
    )

    assert is_dataclass(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.candidate_count == d("3")
    assert report.blocked_count == d("1")
    assert report.watch_count == d("1")
    assert report.pass_count == d("1")
    assert report.top_candidate_id == "rates-stale-sharp"
    assert report.max_revision_pressure_score == d("1.000000")
    assert report.average_revision_pressure_score == d("0.586667")
    assert report.pressure_status == "blocked"
    assert report.reason_codes == (
        "forecast_revision_flat",
        "forecast_revision_up",
        "revision_pressure_blocked",
        "revision_pressure_pass",
        "revision_pressure_watch",
        "sharp_revision_boost",
        "stale_forecast_penalty",
    )
    assert_public_numeric_fields_are_decimal(report)

    assert tuple(row.candidate_id for row in report.rows) == (
        "rates-stale-sharp",
        "sports-moderate",
        "weather-stale-flat",
    )
    top = report.rows[0]
    assert top.rank == d("1")
    assert top.revision_delta == d("0.180000")
    assert top.absolute_revision_delta == d("0.180000")
    assert top.forecast_age_hours == d("60.000000")
    assert top.revision_window_hours == d("24.000000")
    assert top.stale_forecast_penalty == d("0.150000")
    assert top.sharp_revision_boost == d("0.160000")
    assert top.revision_pressure_score == d("1.000000")
    assert top.pressure_status == "blocked"
    assert top.reason_codes == (
        "forecast_revision_up",
        "revision_pressure_blocked",
        "sharp_revision_boost",
        "stale_forecast_penalty",
    )

    middle = report.rows[1]
    assert middle.revision_pressure_score == d("0.560000")
    assert middle.pressure_status == "watch"
    assert middle.reason_codes == ("forecast_revision_up", "revision_pressure_watch")

    bottom = report.rows[2]
    assert bottom.revision_delta == ZERO
    assert bottom.stale_forecast_penalty == d("0.200000")
    assert bottom.sharp_revision_boost == ZERO
    assert bottom.revision_pressure_score == d("0.200000")
    assert bottom.pressure_status == "pass"


def test_stale_forecast_penalty_applies_without_revision() -> None:
    report = pressure_report(
        revision(
            forecast_observed_at=GENERATED_AT - timedelta(hours=72),
            prior_forecast_observed_at=GENERATED_AT - timedelta(hours=96),
            prior_forecast=d("0.500000"),
            current_forecast=d("0.500000"),
        ),
    )

    row = report.rows[0]
    assert row.revision_delta == ZERO
    assert row.stale_forecast_penalty == d("0.200000")
    assert row.sharp_revision_boost == ZERO
    assert row.revision_pressure_score == d("0.200000")
    assert "stale_forecast_penalty" in row.reason_codes


def test_sharp_revision_boost_increases_pressure() -> None:
    report = pressure_report(
        revision(
            candidate_id="sharp",
            prior_forecast=d("0.250000"),
            current_forecast=d("0.450000"),
        ),
        revision(
            candidate_id="moderate",
            prior_forecast=d("0.250000"),
            current_forecast=d("0.340000"),
        ),
    )

    sharp, moderate = report.rows
    assert sharp.candidate_id == "sharp"
    assert sharp.absolute_revision_delta == d("0.200000")
    assert sharp.sharp_revision_boost == d("0.200000")
    assert sharp.revision_pressure_score == d("0.900000")
    assert "sharp_revision_boost" in sharp.reason_codes
    assert moderate.sharp_revision_boost == ZERO
    assert sharp.revision_pressure_score > moderate.revision_pressure_score


def test_payload_serializes_decimals_as_strings_and_revalidates() -> None:
    module = api()
    report = pressure_report(
        revision(),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_forecast_revision_pressure_score_v2_payload(report)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["revision_pressure_score"] == "0.560000"
    assert re.fullmatch(r"[0-9a-f]{64}", payload["derived_validation_digest"])
    assert re.fullmatch(r"[0-9a-f]{64}", payload["rows"][0]["derived_validation_digest"])
    assert not re.search(r":\s*-?\d+\.\d+", encoded)
    assert_no_float_values(payload)
    assert module.strategy_forecast_revision_pressure_score_v2_payload(payload) == payload


def test_dataclasses_are_frozen_decimal_only_and_hard_flags() -> None:
    module = api()
    report = pressure_report(revision())

    assert_public_numeric_fields_are_decimal(config())
    assert_public_numeric_fields_are_decimal(revision())
    assert_public_numeric_fields_are_decimal(report)
    assert report.rows[0].paper_only is True
    assert report.rows[0].report_only is True
    assert report.rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].rank = d("99")

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        revision(readonly=False)
    with pytest.raises(ValueError, match="prior_forecast must be exactly Decimal"):
        revision(prior_forecast=_DecimalSubclass("0.420000"))
    with pytest.raises(ValueError, match="current_forecast must be a Decimal"):
        revision(current_forecast=0.50)
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_strategy_forecast_revision_pressure_score_v2(
            (revision(),),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="forecast_observed_at must be timezone-aware"):
        revision(forecast_observed_at=datetime(2026, 7, 4, 11, 0))
    with pytest.raises(ValueError, match="forecast_observed_at must be timezone-aware"):
        revision(
            forecast_observed_at=datetime(
                2026,
                7,
                4,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )


def test_derived_validation_digest_tampering_is_rejected() -> None:
    module = api()
    report = pressure_report(revision())

    row_tampered = pressure_report(revision())
    object.__setattr__(row_tampered.rows[0], "revision_pressure_score", d("0.010000"))
    with pytest.raises(ValueError, match="derived_validation_digest must match row"):
        module.strategy_forecast_revision_pressure_score_v2_payload(row_tampered)

    report_tampered = pressure_report(revision())
    object.__setattr__(report_tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report"):
        module.strategy_forecast_revision_pressure_score_v2_payload(report_tampered)

    payload = module.strategy_forecast_revision_pressure_score_v2_payload(report)
    row_payload_tampered = {
        **payload,
        "rows": [{**payload["rows"][0], "revision_pressure_score": "0.010000"}],
    }
    with pytest.raises(ValueError, match="derived_validation_digest must match payload row"):
        module.strategy_forecast_revision_pressure_score_v2_payload(row_payload_tampered)


def test_unsafe_payload_keys_and_values_are_rejected() -> None:
    module = api()
    payload = module.strategy_forecast_revision_pressure_score_v2_payload(
        pressure_report(revision()),
    )
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    for unsafe_term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_forecast_revision_pressure_score_v2_payload(
                {**payload, unsafe_term: "plain"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_forecast_revision_pressure_score_v2_payload(
                {**payload, "public_note": f"contains-{unsafe_term}"},
            )


def test_module_has_no_unsafe_surfaces() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_forecast_revision_pressure_score_v2.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    banned_imports = {
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "psycopg",
        "httpx",
        "urllib",
    }
    banned_names = {
        "open",
        "connect",
        "cancel",
        "replace",
        "wallet",
        "order",
        "create_order",
        "place_order",
        "submit_order",
        "trade",
        "auth",
        "login",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_names

    source = path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
        "requests",
        "socket",
        "sqlite3",
        "supabase",
        "psycopg",
    )
    assert [term for term in forbidden_terms if term in source] == []
