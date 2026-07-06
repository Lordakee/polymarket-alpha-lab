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
        "polymarket_alpha_lab.market_forecast_evidence_alignment_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(
    market_slug: str = "btc-above-100k",
    evidence_id: str = "evidence-001",
    *,
    forecast_probability: str = "0.620000",
    evidence_strength_score: str = "0.610000",
    contradiction_count: str = "0",
    stale_evidence_count: str = "0",
    source_quorum_share: str = "1.000000",
    observed_at: datetime = GENERATED_AT,
    reason_codes: tuple[str, ...] = (),
    reference: str | None = None,
):
    digest = api()
    return digest.MarketForecastEvidenceAlignmentInput(
        market_slug=market_slug,
        evidence_id=evidence_id,
        forecast_probability=d(forecast_probability),
        evidence_strength_score=d(evidence_strength_score),
        contradiction_count=d(contradiction_count),
        stale_evidence_count=d(stale_evidence_count),
        source_quorum_share=d(source_quorum_share),
        observed_at=observed_at,
        reason_codes=reason_codes,
        reference=reference,
    )


def report(*items, generated_at: datetime = GENERATED_AT, config=None):
    digest = api()
    return digest.build_market_forecast_evidence_alignment_digest(
        items,
        config=config or digest.MarketForecastEvidenceAlignmentDigestConfig(),
        generated_at=generated_at,
    )


def test_clear_alignment_summarizes_evidence_without_trade_advice():
    digest_report = report(
        evidence(
            evidence_id="evidence-b",
            forecast_probability="0.620000",
            evidence_strength_score="0.600000",
            source_quorum_share="0.800000",
            reason_codes=("forecast_model",),
        ),
        evidence(
            evidence_id="evidence-a",
            forecast_probability="0.640000",
            evidence_strength_score="0.660000",
            source_quorum_share="1.000000",
            reason_codes=("resolution_source",),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.config_version == (
        "market-forecast-evidence-alignment-digest-v0"
    )
    assert digest_report.market_count == d("1")
    assert digest_report.evidence_count == d("2")
    assert digest_report.clear_market_count == d("1")
    assert digest_report.watch_market_count == d("0")
    assert digest_report.blocked_market_count == d("0")
    assert digest_report.status == "clear"
    assert digest_report.reason_codes == (
        "market_forecast_evidence_alignment_clear",
        "forecast_evidence_aligned",
        "source_quorum_met",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    row = digest_report.rows[0]
    assert row.market_slug == "btc-above-100k"
    assert row.status == "clear"
    assert row.forecast_probability == d("0.630000")
    assert row.evidence_strength_score == d("0.630000")
    assert row.alignment_gap == d("0.000000")
    assert row.contradiction_count == d("0")
    assert row.stale_evidence_count == d("0")
    assert row.source_quorum_share == d("0.900000")
    assert row.evidence_count == d("2")
    assert row.latest_observed_at == GENERATED_AT
    assert row.evidence_ids == ("evidence-a", "evidence-b")
    assert row.reason_codes == (
        "forecast_evidence_aligned",
        "input_forecast_model",
        "input_resolution_source",
        "source_quorum_met",
    )


def test_watch_and_blocked_alignment_use_gap_contradictions_staleness_and_quorum():
    digest_report = report(
        evidence(
            "market-watch",
            "watch-1",
            forecast_probability="0.700000",
            evidence_strength_score="0.580000",
            contradiction_count="0",
            stale_evidence_count="1",
            source_quorum_share="0.700000",
        ),
        evidence(
            "market-blocked",
            "blocked-1",
            forecast_probability="0.900000",
            evidence_strength_score="0.500000",
            contradiction_count="2",
            stale_evidence_count="1",
            source_quorum_share="0.400000",
        ),
    )

    assert digest_report.status == "blocked"
    assert digest_report.clear_market_count == d("0")
    assert digest_report.watch_market_count == d("1")
    assert digest_report.blocked_market_count == d("1")
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "market-blocked",
        "market-watch",
    )

    blocked = digest_report.rows[0]
    assert blocked.status == "blocked"
    assert blocked.alignment_gap == d("0.400000")
    assert blocked.reason_codes == (
        "contradiction_pressure_blocked",
        "forecast_evidence_gap_blocked",
        "source_quorum_below_minimum",
        "stale_evidence_present",
    )

    watch = digest_report.rows[1]
    assert watch.status == "watch"
    assert watch.alignment_gap == d("0.120000")
    assert watch.reason_codes == (
        "forecast_evidence_gap_watch",
        "source_quorum_met",
        "stale_evidence_present",
    )


def test_empty_digest_is_deterministic_report_only_clear_summary():
    digest_report = report()

    assert digest_report.market_count == d("0")
    assert digest_report.evidence_count == d("0")
    assert digest_report.clear_market_count == d("0")
    assert digest_report.watch_market_count == d("0")
    assert digest_report.blocked_market_count == d("0")
    assert digest_report.status == "clear"
    assert digest_report.reason_codes == ("empty_market_forecast_evidence_alignment_inputs",)
    assert digest_report.rows == ()
    assert digest_report.reason_rollups == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_reason_rollups_are_deterministic_and_ratio_based():
    digest_report = report(
        evidence(
            "z-market",
            "z-1",
            forecast_probability="0.800000",
            evidence_strength_score="0.550000",
        ),
        evidence(
            "a-market",
            "a-1",
            forecast_probability="0.500000",
            evidence_strength_score="0.500000",
            reason_codes=("alpha", "zeta"),
        ),
    )

    assert tuple(row.market_slug for row in digest_report.rows) == (
        "z-market",
        "a-market",
    )
    assert tuple(
        (rollup.reason_code, rollup.market_count, rollup.market_ratio)
        for rollup in digest_report.reason_rollups
    ) == (
        ("forecast_evidence_aligned", d("1"), d("0.500000")),
        ("forecast_evidence_gap_blocked", d("1"), d("0.500000")),
        ("source_quorum_met", d("2"), d("1.000000")),
    )


def test_datetimes_normalize_to_utc_aware_values():
    eastern = timezone(timedelta(hours=-4))
    digest_report = report(
        evidence(
            "market-time",
            "time-1",
            observed_at=datetime(2026, 7, 2, 8, 0, tzinfo=eastern),
        ),
        generated_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
    )

    assert digest_report.generated_at == datetime(2026, 7, 2, 12, 30, tzinfo=UTC)
    assert digest_report.rows[0].latest_observed_at == datetime(
        2026,
        7,
        2,
        12,
        0,
        tzinfo=UTC,
    )


def test_validation_rejects_naive_datetimes():
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        evidence(observed_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(evidence(), generated_at=datetime(2026, 7, 2, 12, 30))


def test_validation_rejects_datetime_subclasses_and_none_offset_tzinfo():
    class DateTimeSubclass(datetime):
        pass

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        evidence(
            observed_at=DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(
            evidence(),
            generated_at=DateTimeSubclass(2026, 7, 2, 12, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        evidence(observed_at=datetime(2026, 7, 2, 12, 0, tzinfo=NoneOffsetTz()))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            evidence(),
            generated_at=datetime(2026, 7, 2, 12, 30, tzinfo=NoneOffsetTz()),
        )


def test_payload_serializes_decimal_strings_redacts_references_and_has_no_floats():
    digest = api()
    digest_report = report(
        evidence(
            "market-json",
            "json-1",
            forecast_probability="0.700000",
            evidence_strength_score="0.650000",
            reference="token=abc123 private_key=secret",
        ),
    )

    payload = digest.market_forecast_evidence_alignment_digest_payload(digest_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1"
    assert payload["rows"][0]["forecast_probability"] == "0.700000"
    assert payload["rows"][0]["reference"] == "<redacted>"
    assert "abc123" not in encoded
    assert "secret" not in encoded
    assert all(type(value) is not float for value in _walk(payload))
    assert all(type(value) is not int for value in _walk(payload))


def test_report_exposes_tamper_evident_derived_validation_digest():
    digest = api()
    digest_report = report(
        evidence(
            "market-digest",
            "digest-1",
            forecast_probability="0.760000",
            evidence_strength_score="0.510000",
            contradiction_count="2",
        ),
    )

    assert len(digest_report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in digest_report.derived_validation_digest
    )

    payload = digest.market_forecast_evidence_alignment_digest_payload(digest_report)
    assert payload["derived_validation_digest"] == (
        digest_report.derived_validation_digest
    )
    assert all(type(value) is not float for value in _walk(payload))
    assert all(type(value) is not int for value in _walk(payload))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest_report, derived_validation_digest="0" * 64)

    tampered_report = replace(digest_report)
    object.__setattr__(tampered_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        digest.market_forecast_evidence_alignment_digest_payload(tampered_report)


def test_payload_redacts_sensitive_reference_fragments_deterministically():
    digest = api()
    digest_report = report(
        evidence(
            "market-sensitive",
            "sensitive-1",
            reference="https://example.test/path?api_key=visible-key",
        ),
        evidence(
            "market-sensitive",
            "sensitive-2",
            reference="https://example.test/path?session=abc123",
        ),
    )

    payload = digest.market_forecast_evidence_alignment_digest_payload(digest_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["rows"][0]["reference"] == "<redacted>"
    assert "api_key" not in encoded.lower()
    assert "visible-key" not in encoded
    assert "session" not in encoded.lower()
    assert "abc123" not in encoded


def test_validation_rejects_sensitive_public_identifiers_and_reason_labels():
    with pytest.raises(ValueError, match="market_slug must not contain sensitive fragments"):
        evidence(market_slug="market-token-abc123")
    with pytest.raises(ValueError, match="evidence_id must not contain sensitive fragments"):
        evidence(evidence_id="private_key-source")
    with pytest.raises(ValueError, match="reason_codes must not contain sensitive fragments"):
        evidence(reason_codes=("api_key_visible",))


def test_validation_rejects_unsafe_live_persistent_surfaces():
    for unsafe_fragment in (
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "live",
    ):
        with pytest.raises(
            ValueError,
            match="must not contain sensitive fragments|has unsafe value",
        ):
            evidence(market_slug=f"market-{unsafe_fragment}-surface")


def test_payload_rejects_bypassed_unsafe_surface_values_before_serializing():
    digest = api()
    digest_report = report(evidence("market-safe", "safe-1"))
    row = replace(digest_report.rows[0])
    object.__setattr__(row, "market_slug", "market-network-surface")
    tampered_report = replace(digest_report)
    object.__setattr__(tampered_report, "rows", (row,))

    with pytest.raises(ValueError, match="unsafe value|sensitive fragments"):
        digest.market_forecast_evidence_alignment_digest_payload(tampered_report)


def test_validation_rejects_floats_nonfinite_decimals_duplicates_and_unsafe_flags():
    digest = api()

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        digest.MarketForecastEvidenceAlignmentInput(
            market_slug="market-bad",
            evidence_id="source",
            forecast_probability=0.5,
            evidence_strength_score=d("0.500000"),
            contradiction_count=d("0"),
            stale_evidence_count=d("0"),
            source_quorum_share=d("1.000000"),
            observed_at=GENERATED_AT,
            reason_codes=(),
        )
    with pytest.raises(ValueError, match="forecast_probability must be finite"):
        evidence(forecast_probability="NaN")
    with pytest.raises(ValueError, match="duplicate evidence_id"):
        report(evidence("market-dupe", "source"), evidence("market-dupe", "source"))
    with pytest.raises(ValueError, match="watch_alignment_gap"):
        digest.MarketForecastEvidenceAlignmentDigestConfig(
            watch_alignment_gap=d("0.300000"),
            blocked_alignment_gap=d("0.200000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(evidence("market-flags", "source"), paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        digest.MarketForecastEvidenceAlignmentDigestConfig(readonly=False)


def test_validation_rejects_fractional_decimal_counts():
    digest = api()

    with pytest.raises(ValueError, match="contradiction_count must be a whole count"):
        evidence(contradiction_count="0.5")
    with pytest.raises(ValueError, match="watch_contradiction_count must be a whole count"):
        digest.MarketForecastEvidenceAlignmentDigestConfig(
            watch_contradiction_count=d("0.5"),
        )


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict():
    digest = api()

    class DecimalSubclass(Decimal):
        pass

    row = evidence("market-frozen", "source")
    with pytest.raises(FrozenInstanceError):
        row.evidence_id = "other"  # type: ignore[misc]
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        digest.MarketForecastEvidenceAlignmentInput(
            market_slug="market-bad-subclass",
            evidence_id="source",
            forecast_probability=DecimalSubclass("0.500000"),
            evidence_strength_score=d("0.500000"),
            contradiction_count=d("0"),
            stale_evidence_count=d("0"),
            source_quorum_share=d("1.000000"),
            observed_at=GENERATED_AT,
            reason_codes=(),
        )


def test_public_rows_reject_nondeterministic_reason_code_order():
    digest = api()

    with pytest.raises(ValueError, match="reason_codes must use deterministic order"):
        digest.MarketForecastEvidenceAlignmentRow(
            market_slug="market-sequence",
            status="watch",
            forecast_probability=d("0.700000"),
            evidence_strength_score=d("0.580000"),
            contradiction_count=d("0"),
            stale_evidence_count=d("1"),
            source_quorum_share=d("1.000000"),
            alignment_gap=d("0.120000"),
            evidence_count=d("1"),
            latest_observed_at=GENERATED_AT,
            evidence_ids=("source",),
            reason_codes=(
                "stale_evidence_present",
                "forecast_evidence_gap_watch",
                "source_quorum_met",
            ),
            reference=None,
        )


def test_module_scope_has_no_forbidden_live_network_file_or_advice_surface():
    source_text = Path(
        "src/polymarket_alpha_lab/market_forecast_evidence_alignment_digest.py",
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
        "live",
        "persist",
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
