from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_probability_source_divergence_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def forecast(
    market_id: str,
    source_id: str,
    source_family: str,
    probability: str,
    *,
    confidence: str = "0.800000",
    observed_at: datetime = GENERATED_AT,
    reason_codes: tuple[str, ...] = ("team_forecast",),
):
    digest = api()
    return digest.MarketProbabilitySourceForecast(
        market_id=market_id,
        source_id=source_id,
        source_family=source_family,
        forecast_probability=d(probability),
        confidence=d(confidence),
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def market_input(
    market_id: str,
    implied: str,
    *forecasts,
):
    digest = api()
    return digest.MarketProbabilitySourceDivergenceInput(
        market_id=market_id,
        market_implied_probability=d(implied),
        forecasts=forecasts,
    )


def report(*rows, generated_at: datetime = GENERATED_AT):
    digest = api()
    return digest.build_market_probability_source_divergence_digest(
        rows,
        config=digest.MarketProbabilitySourceDivergenceDigestConfig(),
        generated_at=generated_at,
    )


def test_digest_summarizes_probability_family_recency_and_confidence_divergence():
    stale_observed_at = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)
    digest_report = report(
        market_input(
            "market-blocked",
            "0.700000",
            forecast("market-blocked", "model", "model", "0.400000", confidence="0.900000"),
            forecast("market-blocked", "news", "news", "0.900000", confidence="0.300000"),
            forecast(
                "market-blocked",
                "research",
                "research",
                "0.100000",
                confidence="0.600000",
                observed_at=stale_observed_at,
                reason_codes=("source_forecast",),
            ),
        ),
        market_input(
            "market-clear",
            "0.520000",
            forecast("market-clear", "team", "team", "0.510000"),
            forecast("market-clear", "source", "source", "0.530000"),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.market_count == d("2")
    assert digest_report.clear_market_count == d("1")
    assert digest_report.blocked_market_count == d("1")
    assert digest_report.divergent_market_count == d("1")
    assert digest_report.divergent_market_ratio == d("0.500000")
    assert digest_report.status == "blocked"
    assert digest_report.reason_codes == (
        "market_probability_source_divergence_blocked",
        "market_source_family_disagreement_present",
        "market_forecast_recency_degraded",
        "market_confidence_dispersion_present",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    blocked = digest_report.rows[0]
    assert blocked.market_id == "market-blocked"
    assert blocked.status == "blocked"
    assert blocked.market_implied_probability == d("0.700000")
    assert blocked.recency_weighted_forecast_probability == d("0.477778")
    assert blocked.probability_gap == d("0.222222")
    assert blocked.source_count == d("3")
    assert blocked.source_family_count == d("3")
    assert blocked.stale_source_count == d("1")
    assert blocked.source_family_disagreement == d("0.800000")
    assert blocked.confidence_dispersion == d("0.600000")
    assert blocked.reason_codes == (
        "market_probability_source_gap_blocked",
        "source_family_disagreement_blocked",
        "forecast_recency_degraded",
        "confidence_dispersion_blocked",
    )

    assert tuple(row.market_id for row in digest_report.rows) == (
        "market-blocked",
        "market-clear",
    )
    assert tuple(rollup.reason_code for rollup in digest_report.reason_rollups) == (
        "confidence_dispersion_blocked",
        "forecast_recency_degraded",
        "market_probability_aligned",
        "market_probability_source_gap_blocked",
        "source_family_disagreement_blocked",
    )


def test_datetimes_normalize_to_utc_aware_values():
    eastern = timezone(timedelta(hours=-4))
    observed_at = datetime(2026, 7, 2, 8, 0, tzinfo=eastern)
    generated_at = datetime(2026, 7, 2, 8, 30, tzinfo=UTC)
    digest_report = report(
        market_input(
            "market-time",
            "0.500000",
            forecast("market-time", "source", "team", "0.480000", observed_at=observed_at),
        ),
        generated_at=generated_at,
    )

    assert digest_report.generated_at == datetime(2026, 7, 2, 8, 30, tzinfo=UTC)
    assert digest_report.rows[0].latest_observed_at == datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    source = Path(api().__file__).read_text()
    tree = ast.parse(source)
    assert all(
        not (isinstance(node, ast.Constant) and type(node.value) is float)
        for node in ast.walk(tree)
    )
    assert all(
        not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "float"
        )
        for node in ast.walk(tree)
    )
    assert "replace(tzinfo" not in source


def test_datetimes_reject_naive_none_offset_and_subclass_values():
    digest = api()

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    class DerivedDatetime(datetime):
        pass

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        forecast(
            "market-naive-observed",
            "source",
            "team",
            "0.500000",
            observed_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        forecast(
            "market-none-offset",
            "source",
            "team",
            "0.500000",
            observed_at=datetime(2026, 7, 2, 12, 0, tzinfo=NoneOffsetTz()),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            market_input(
                "market-naive-generated",
                "0.500000",
                forecast("market-naive-generated", "source", "team", "0.500000"),
            ),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        digest.MarketProbabilitySourceForecast(
            market_id="market-derived-datetime",
            source_id="source",
            source_family="team",
            forecast_probability=d("0.500000"),
            confidence=d("0.800000"),
            observed_at=DerivedDatetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            reason_codes=("team_forecast",),
        )


def test_payload_serializes_decimals_and_iso_datetimes_without_floats():
    payload = api().market_probability_source_divergence_digest_payload(
        report(
            market_input(
                "market-json",
                "0.600000",
                forecast("market-json", "source", "team", "0.540000"),
            ),
        ),
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1"
    assert payload["rows"][0]["market_implied_probability"] == "0.600000"
    assert payload["rows"][0]["probability_gap"] == "0.060000"
    assert isinstance(payload["rows"][0]["probability_gap"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == (
        api().market_probability_source_divergence_digest_payload(payload)[
            "derived_validation_digest"
        ]
    )
    json.dumps(payload)

    def walk(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from walk(item)
        elif isinstance(value, list):
            for item in value:
                yield from walk(item)
        else:
            yield value

    assert all(type(value) is not float for value in walk(payload))


def test_report_uses_tamper_evident_derived_validation_digest():
    digest = api()
    digest_report = report(
        market_input(
            "market-validation",
            "0.620000",
            forecast("market-validation", "source-a", "team", "0.580000"),
            forecast("market-validation", "source-b", "model", "0.610000"),
        ),
    )

    assert len(digest_report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in digest_report.derived_validation_digest
    )

    payload = digest.market_probability_source_divergence_digest_payload(digest_report)
    assert payload["derived_validation_digest"] == digest_report.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(
            digest_report,
            generated_at=GENERATED_AT + timedelta(seconds=1),
        )


def test_public_payload_rejects_bad_decimal_digest_flags_and_unsafe_surfaces():
    digest = api()
    payload = digest.market_probability_source_divergence_digest_payload(
        report(
            market_input(
                "market-payload",
                "0.600000",
                forecast("market-payload", "source", "team", "0.540000"),
            ),
        ),
    )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        digest.market_probability_source_divergence_digest_payload(missing_digest)

    tampered = dict(payload)
    tampered["market_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        digest.market_probability_source_divergence_digest_payload(tampered)

    bad_decimal = dict(payload)
    bad_decimal["market_count"] = d("1")
    with pytest.raises(ValueError, match="market_count must be a Decimal-derived string"):
        digest.market_probability_source_divergence_digest_payload(bad_decimal)

    bad_flag = dict(payload)
    bad_flag["readonly"] = False
    with pytest.raises(ValueError, match="readonly must be True"):
        digest.market_probability_source_divergence_digest_payload(bad_flag)

    unsafe_keys = (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_client",
        "database_url",
        "persist_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            digest.market_probability_source_divergence_digest_payload(unsafe_payload)

    unsafe_values = (
        "live mode enabled",
        "auth token configured",
        "wallet transfer configured",
        "submit order configured",
        "network request configured",
        "database writer configured",
        "persist report configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["rows"] = [dict(payload["rows"][0], market_id=unsafe_value)]
        with pytest.raises(ValueError, match="unsafe"):
            digest.market_probability_source_divergence_digest_payload(unsafe_payload)


def test_deterministic_sorting_and_stable_reason_rollups():
    digest_report = report(
        market_input(
            "market-watch-b",
            "0.500000",
            forecast("market-watch-b", "source-b", "model", "0.600000"),
        ),
        market_input(
            "market-blocked",
            "0.900000",
            forecast("market-blocked", "source-a", "model", "0.300000"),
        ),
        market_input(
            "market-watch-a",
            "0.500000",
            forecast("market-watch-a", "source-c", "model", "0.600000"),
        ),
    )

    assert tuple(row.market_id for row in digest_report.rows) == (
        "market-blocked",
        "market-watch-a",
        "market-watch-b",
    )
    assert digest_report.reason_codes == ("market_probability_source_divergence_blocked",)
    assert tuple(
        (rollup.reason_code, rollup.market_count, rollup.market_ratio)
        for rollup in digest_report.reason_rollups
    ) == (
        ("market_probability_source_gap_watch", d("2"), d("0.666667")),
        ("market_probability_source_gap_blocked", d("1"), d("0.333333")),
    )


def test_empty_digest_and_hard_flags_are_report_only():
    digest = api()
    digest_report = report()

    assert digest_report.market_count == d("0")
    assert digest_report.divergent_market_ratio is None
    assert digest_report.status == "clear"
    assert digest_report.reason_codes == (
        "empty_market_probability_source_divergence_inputs",
    )
    assert digest_report.rows == ()
    assert digest_report.reason_rollups == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    row = forecast("market-flags", "source", "team", "0.500000")
    with pytest.raises(FrozenInstanceError):
        row.confidence = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        digest.MarketProbabilitySourceDivergenceDigestConfig(readonly=False)


def test_validation_rejects_float_mismatched_market_duplicates_and_bad_config():
    digest = api()
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        digest.MarketProbabilitySourceForecast(
            market_id="market-bad",
            source_id="source",
            source_family="team",
            forecast_probability=0.5,
            confidence=d("0.800000"),
            observed_at=GENERATED_AT,
            reason_codes=("team_forecast",),
        )

    with pytest.raises(ValueError, match="forecast market_id must match"):
        market_input(
            "market-a",
            "0.500000",
            forecast("market-b", "source", "team", "0.500000"),
        )

    with pytest.raises(ValueError, match="duplicate source_id"):
        market_input(
            "market-dupe",
            "0.500000",
            forecast("market-dupe", "source", "team", "0.500000"),
            forecast("market-dupe", "source", "model", "0.600000"),
        )

    with pytest.raises(ValueError, match="duplicate market_id"):
        report(
            market_input("market-dupe", "0.500000"),
            market_input("market-dupe", "0.600000"),
        )

    duplicate_row = report(
        market_input(
            "market-report-dupe",
            "0.500000",
            forecast("market-report-dupe", "source", "team", "0.500000"),
        ),
    ).rows[0]
    with pytest.raises(ValueError, match="duplicate market_id"):
        digest.MarketProbabilitySourceDivergenceDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                digest.DEFAULT_MARKET_PROBABILITY_SOURCE_DIVERGENCE_DIGEST_CONFIG_VERSION
            ),
            market_count=d("2"),
            clear_market_count=d("2"),
            watch_market_count=d("0"),
            blocked_market_count=d("0"),
            divergent_market_count=d("0"),
            divergent_market_ratio=d("0.000000"),
            status="clear",
            reason_codes=("market_probability_source_divergence_clear",),
            rows=(duplicate_row, duplicate_row),
            reason_rollups=(
                digest.MarketProbabilitySourceReasonRollup(
                    reason_code="market_probability_aligned",
                    market_count=d("2"),
                    market_ratio=d("1.000000"),
                ),
            ),
        )

    sorted_report = report(
        market_input(
            "market-rollup-watch",
            "0.500000",
            forecast("market-rollup-watch", "source-watch", "team", "0.600000"),
        ),
        market_input(
            "market-rollup-blocked",
            "0.900000",
            forecast("market-rollup-blocked", "source-blocked", "team", "0.300000"),
        ),
    )
    with pytest.raises(ValueError, match="rows must use deterministic ordering"):
        digest.MarketProbabilitySourceDivergenceDigestReport(
            generated_at=sorted_report.generated_at,
            config_version=sorted_report.config_version,
            market_count=sorted_report.market_count,
            clear_market_count=sorted_report.clear_market_count,
            watch_market_count=sorted_report.watch_market_count,
            blocked_market_count=sorted_report.blocked_market_count,
            divergent_market_count=sorted_report.divergent_market_count,
            divergent_market_ratio=sorted_report.divergent_market_ratio,
            status=sorted_report.status,
            reason_codes=sorted_report.reason_codes,
            rows=tuple(reversed(sorted_report.rows)),
            reason_rollups=sorted_report.reason_rollups,
        )

    with pytest.raises(ValueError, match="duplicate reason_code"):
        digest.MarketProbabilitySourceDivergenceDigestReport(
            generated_at=sorted_report.generated_at,
            config_version=sorted_report.config_version,
            market_count=sorted_report.market_count,
            clear_market_count=sorted_report.clear_market_count,
            watch_market_count=sorted_report.watch_market_count,
            blocked_market_count=sorted_report.blocked_market_count,
            divergent_market_count=sorted_report.divergent_market_count,
            divergent_market_ratio=sorted_report.divergent_market_ratio,
            status=sorted_report.status,
            reason_codes=sorted_report.reason_codes,
            rows=sorted_report.rows,
            reason_rollups=(
                sorted_report.reason_rollups[0],
                sorted_report.reason_rollups[0],
            ),
        )

    with pytest.raises(ValueError, match="reason_rollups must use deterministic ordering"):
        digest.MarketProbabilitySourceDivergenceDigestReport(
            generated_at=sorted_report.generated_at,
            config_version=sorted_report.config_version,
            market_count=sorted_report.market_count,
            clear_market_count=sorted_report.clear_market_count,
            watch_market_count=sorted_report.watch_market_count,
            blocked_market_count=sorted_report.blocked_market_count,
            divergent_market_count=sorted_report.divergent_market_count,
            divergent_market_ratio=sorted_report.divergent_market_ratio,
            status=sorted_report.status,
            reason_codes=sorted_report.reason_codes,
            rows=sorted_report.rows,
            reason_rollups=tuple(reversed(sorted_report.reason_rollups)),
        )

    with pytest.raises(ValueError, match="must not exceed"):
        digest.MarketProbabilitySourceDivergenceDigestConfig(
            watch_probability_gap=d("0.200000"),
            blocked_probability_gap=d("0.100000"),
        )

    with pytest.raises(ValueError, match="recency_half_life_seconds must be positive"):
        digest.MarketProbabilitySourceDivergenceDigestConfig(
            recency_half_life_seconds=d("0.0000001"),
        )


def test_dataclass_subclasses_are_rejected():
    digest = api()

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ForecastSubclass(digest.MarketProbabilitySourceForecast):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(digest.MarketProbabilitySourceDivergenceInput):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class RowSubclass(digest.MarketProbabilitySourceDivergenceRow):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class RollupSubclass(digest.MarketProbabilitySourceReasonRollup):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ReportSubclass(digest.MarketProbabilitySourceDivergenceDigestReport):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(digest.MarketProbabilitySourceDivergenceDigestConfig):
            pass


def test_module_scope_has_no_forbidden_live_surface():
    source = Path(
        "src/polymarket_alpha_lab/market_probability_source_divergence_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "network",
        "database",
        "advice",
        "recommendation",
        "market_slug",
        "question",
        "payload_json",
        "open(",
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
