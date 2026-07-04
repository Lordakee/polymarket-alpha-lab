from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_forecast_source_blend_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def source(
    candidate_id: str,
    source_id: str,
    source_kind: str,
    probability: str,
    reliability: str,
    *,
    observed_at: datetime = GENERATED_AT,
    reason_codes: tuple[str, ...] = (),
    reference: str | None = None,
):
    digest = api()
    return digest.StrategyForecastBlendSource(
        candidate_id=candidate_id,
        source_id=source_id,
        source_kind=source_kind,
        probability=d(probability),
        reliability_weight=d(reliability),
        observed_at=observed_at,
        reason_codes=reason_codes,
        reference=reference,
    )


def candidate(
    candidate_id: str,
    *,
    sources=(),
    model_forecast: str | None = "0.600000",
    team_forecast: str | None = "0.580000",
    market_price: str | None = "0.550000",
):
    digest = api()
    return digest.StrategyForecastBlendCandidate(
        candidate_id=candidate_id,
        model_forecast=None if model_forecast is None else d(model_forecast),
        team_forecast=None if team_forecast is None else d(team_forecast),
        market_price=None if market_price is None else d(market_price),
        sources=sources,
    )


def report(*candidates, generated_at: datetime = GENERATED_AT, config=None):
    digest = api()
    return digest.build_strategy_forecast_source_blend_digest(
        candidates,
        config=config or digest.StrategyForecastSourceBlendDigestConfig(),
        generated_at=generated_at,
    )


def test_digest_blends_core_forecasts_and_source_reliability_weights():
    digest_report = report(
        candidate(
            "candidate-a",
            sources=(
                source(
                    "candidate-a",
                    "team-quality",
                    "team",
                    "0.620000",
                    "0.700000",
                    reason_codes=("manual_team_forecast",),
                ),
                source(
                    "candidate-a",
                    "model-v1",
                    "model",
                    "0.560000",
                    "0.900000",
                    reason_codes=("model_forecast",),
                ),
                source(
                    "candidate-a",
                    "market-mid",
                    "market",
                    "0.500000",
                    "0.400000",
                    reason_codes=("market_price",),
                ),
            ),
            model_forecast="0.560000",
            team_forecast="0.620000",
            market_price="0.500000",
        ),
        candidate(
            "candidate-clear",
            sources=(
                source("candidate-clear", "model", "model", "0.500000", "0.800000"),
                source("candidate-clear", "team", "team", "0.510000", "0.800000"),
            ),
            model_forecast="0.500000",
            team_forecast="0.510000",
            market_price="0.505000",
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.config_version == (
        "strategy-forecast-source-blend-digest-v0"
    )
    assert digest_report.candidate_count == d("2")
    assert digest_report.clear_candidate_count == d("1")
    assert digest_report.watch_candidate_count == d("1")
    assert digest_report.blocked_candidate_count == d("0")
    assert digest_report.capped_candidate_count == d("0")
    assert digest_report.capped_candidate_ratio == d("0.000000")
    assert digest_report.status == "watch"
    assert digest_report.reason_codes == (
        "strategy_forecast_source_blend_watch",
        "source_weighted_blend_available",
        "forecast_source_disagreement_present",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    row = digest_report.rows[0]
    assert row.candidate_id == "candidate-a"
    assert row.status == "watch"
    assert row.model_forecast == d("0.560000")
    assert row.team_forecast == d("0.620000")
    assert row.market_price == d("0.500000")
    assert row.source_weighted_probability == d("0.569000")
    assert row.blended_probability == d("0.567800")
    assert row.disagreement_gap == d("0.120000")
    assert row.applied_disagreement_cap == d("0.000000")
    assert row.candidate_probability == d("0.567800")
    assert row.source_count == d("3")
    assert row.source_reliability_weight == d("2.000000")
    assert row.reason_codes == (
        "source_weighted_blend_available",
        "forecast_source_disagreement_watch",
    )
    assert tuple(source_row.source_id for source_row in row.sources) == (
        "model-v1",
        "team-quality",
        "market-mid",
    )


def test_disagreement_cap_limits_candidate_probability_toward_market_price():
    digest_report = report(
        candidate(
            "candidate-capped",
            sources=(
                source("candidate-capped", "model", "model", "0.920000", "1.000000"),
                source("candidate-capped", "team", "team", "0.880000", "1.000000"),
                source("candidate-capped", "market", "market", "0.200000", "0.500000"),
            ),
            model_forecast="0.920000",
            team_forecast="0.880000",
            market_price="0.200000",
        ),
    )

    row = digest_report.rows[0]
    assert digest_report.status == "blocked"
    assert digest_report.blocked_candidate_count == d("1")
    assert digest_report.capped_candidate_count == d("1")
    assert digest_report.capped_candidate_ratio == d("1.000000")
    assert row.status == "blocked"
    assert row.source_weighted_probability == d("0.760000")
    assert row.blended_probability == d("0.732000")
    assert row.disagreement_gap == d("0.720000")
    assert row.applied_disagreement_cap == d("0.250000")
    assert row.candidate_probability == d("0.450000")
    assert row.reason_codes == (
        "source_weighted_blend_available",
        "forecast_source_disagreement_blocked",
        "disagreement_cap_applied",
    )


def test_missing_sources_are_reported_without_trade_advice():
    digest_report = report(
        candidate(
            "candidate-missing",
            sources=(),
            model_forecast="0.490000",
            team_forecast=None,
            market_price=None,
        ),
    )

    row = digest_report.rows[0]
    assert digest_report.status == "watch"
    assert row.status == "watch"
    assert row.source_weighted_probability is None
    assert row.blended_probability == d("0.490000")
    assert row.candidate_probability == d("0.490000")
    assert row.source_count == d("0")
    assert row.reason_codes == ("missing_forecast_sources",)


def test_empty_digest_is_deterministic_report_only_clear_summary():
    digest_report = report()

    assert digest_report.candidate_count == d("0")
    assert digest_report.clear_candidate_count == d("0")
    assert digest_report.watch_candidate_count == d("0")
    assert digest_report.blocked_candidate_count == d("0")
    assert digest_report.capped_candidate_count == d("0")
    assert digest_report.capped_candidate_ratio is None
    assert digest_report.status == "clear"
    assert digest_report.reason_codes == ("empty_strategy_forecast_blend_inputs",)
    assert digest_report.rows == ()
    assert digest_report.reason_rollups == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_deterministic_sorting_and_reason_rollups():
    digest_report = report(
        candidate(
            "candidate-watch-z",
            sources=(source("candidate-watch-z", "model", "model", "0.600000", "1.000000"),),
            model_forecast="0.600000",
            team_forecast=None,
            market_price="0.500000",
        ),
        candidate(
            "candidate-blocked",
            sources=(source("candidate-blocked", "model", "model", "0.900000", "1.000000"),),
            model_forecast="0.900000",
            team_forecast="0.900000",
            market_price="0.100000",
        ),
        candidate(
            "candidate-watch-a",
            sources=(source("candidate-watch-a", "team", "team", "0.600000", "1.000000"),),
            model_forecast=None,
            team_forecast="0.600000",
            market_price="0.500000",
        ),
    )

    assert tuple(row.candidate_id for row in digest_report.rows) == (
        "candidate-blocked",
        "candidate-watch-a",
        "candidate-watch-z",
    )
    assert digest_report.reason_codes == (
        "strategy_forecast_source_blend_blocked",
        "source_weighted_blend_available",
        "forecast_source_disagreement_present",
        "disagreement_cap_limited_candidates",
    )
    assert tuple(
        (rollup.reason_code, rollup.candidate_count, rollup.candidate_ratio)
        for rollup in digest_report.reason_rollups
    ) == (
        ("source_weighted_blend_available", d("3"), d("1.000000")),
        ("forecast_source_disagreement_watch", d("2"), d("0.666667")),
        ("disagreement_cap_applied", d("1"), d("0.333333")),
        ("forecast_source_disagreement_blocked", d("1"), d("0.333333")),
    )


def test_datetimes_normalize_to_utc_aware_values():
    eastern = timezone(timedelta(hours=-4))
    digest_report = report(
        candidate(
            "candidate-time",
            sources=(
                source(
                    "candidate-time",
                    "source",
                    "model",
                    "0.500000",
                    "0.900000",
                    observed_at=datetime(2026, 7, 2, 8, 0, tzinfo=eastern),
                ),
            ),
        ),
        generated_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
    )

    assert digest_report.generated_at == datetime(2026, 7, 2, 8, 30, tzinfo=UTC)
    assert digest_report.rows[0].latest_observed_at == datetime(
        2026,
        7,
        2,
        12,
        0,
        tzinfo=UTC,
    )


def test_naive_datetimes_are_rejected_for_phase1_boundary():
    digest = api()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 2, 8, 30))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        digest.StrategyForecastBlendSource(
            candidate_id="candidate-time",
            source_id="source",
            source_kind="model",
            probability=d("0.500000"),
            reliability_weight=d("1.000000"),
            observed_at=datetime(2026, 7, 2, 8, 0),
            reason_codes=(),
        )


def test_fractional_source_reliability_weight_is_preserved():
    digest_report = report(
        candidate(
            "candidate-fractional-weight",
            sources=(
                source(
                    "candidate-fractional-weight",
                    "model",
                    "model",
                    "0.500000",
                    "0.333333",
                ),
                source(
                    "candidate-fractional-weight",
                    "team",
                    "team",
                    "0.600000",
                    "0.333333",
                ),
            ),
        ),
    )

    assert digest_report.rows[0].source_reliability_weight == d("0.666666")


def test_reason_codes_normalize_to_declared_order():
    digest = api()

    blend_source = digest.StrategyForecastBlendSource(
        candidate_id="candidate-reasons",
        source_id="source",
        source_kind="model",
        probability=d("0.500000"),
        reliability_weight=d("1.000000"),
        observed_at=GENERATED_AT,
        reason_codes=("market_price", "model_forecast"),
    )

    assert blend_source.reason_codes == ("model_forecast", "market_price")


def test_reference_redaction_covers_unsafe_surface_terms():
    digest_report = report(
        candidate(
            "candidate-redaction",
            sources=(
                source(
                    "candidate-redaction",
                    "source",
                    "research",
                    "0.600000",
                    "1.000000",
                    reference="wal" + "let=0xabc123",
                ),
            ),
            model_forecast="0.600000",
            team_forecast=None,
            market_price="0.500000",
        ),
    )

    payload = api().strategy_forecast_source_blend_digest_payload(digest_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["rows"][0]["sources"][0]["reference"] == "<redacted>"
    assert "0xabc123" not in encoded


def test_payload_serializes_decimal_strings_redacts_references_and_has_no_floats():
    digest = api()
    digest_report = report(
        candidate(
            "candidate-json",
            sources=(
                source(
                    "candidate-json",
                    "model",
                    "model",
                    "0.600000",
                    "1.000000",
                    reference="private_key=abc123 token=secret",
                ),
            ),
            model_forecast="0.600000",
            team_forecast=None,
            market_price="0.500000",
        ),
    )

    payload = digest.strategy_forecast_source_blend_digest_payload(digest_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["candidate_probability"] == "0.571429"
    assert payload["rows"][0]["sources"][0]["reference"] == "<redacted>"
    assert "abc123" not in encoded
    assert "secret" not in encoded
    assert '"0.571429"' in encoded
    assert all(type(value) is not float for value in _walk(payload))


def test_validation_rejects_floats_nonfinite_decimals_duplicates_and_unsafe_flags():
    digest = api()

    with pytest.raises(ValueError, match="probability must be a Decimal"):
        digest.StrategyForecastBlendSource(
            candidate_id="candidate-bad",
            source_id="source",
            source_kind="model",
            probability=0.5,
            reliability_weight=d("1.000000"),
            observed_at=GENERATED_AT,
            reason_codes=(),
        )
    with pytest.raises(ValueError, match="model_forecast must be finite"):
        candidate("candidate-nan", model_forecast=None). __class__(
            candidate_id="candidate-nan",
            model_forecast=Decimal("NaN"),
            team_forecast=None,
            market_price=None,
            sources=(),
        )
    with pytest.raises(ValueError, match="duplicate source_id"):
        candidate(
            "candidate-dupe",
            sources=(
                source("candidate-dupe", "source", "model", "0.500000", "0.800000"),
                source("candidate-dupe", "source", "team", "0.600000", "0.700000"),
            ),
        )
    with pytest.raises(ValueError, match="source candidate_id must match"):
        candidate(
            "candidate-a",
            sources=(source("candidate-b", "source", "model", "0.500000", "0.800000"),),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(source("candidate-flags", "source", "model", "0.500000", "0.800000"), paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        digest.StrategyForecastSourceBlendDigestConfig(readonly=False)


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict():
    digest = api()

    class DecimalSubclass(Decimal):
        pass

    row = source("candidate-frozen", "source", "model", "0.500000", "0.800000")
    with pytest.raises(FrozenInstanceError):
        row.source_id = "other"  # type: ignore[misc]
    with pytest.raises(ValueError, match="probability must be a Decimal"):
        digest.StrategyForecastBlendSource(
            candidate_id="candidate-bad-subclass",
            source_id="source",
            source_kind="model",
            probability=DecimalSubclass("0.500000"),
            reliability_weight=d("1.000000"),
            observed_at=GENERATED_AT,
            reason_codes=(),
        )


def test_module_scope_has_no_forbidden_live_network_file_or_advice_surface():
    source_text = Path(
        "src/polymarket_alpha_lab/strategy_forecast_source_blend_digest.py",
    ).read_text(encoding="utf-8")
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
        "network",
        "database",
        "advice",
        "open(",
        "requests",
        "http",
        "socket",
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value
