from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_forecast_source_recency_consensus_digest import (
    MarketForecastSourceRecencyConsensusConfig,
    MarketForecastSourceRecencyConsensusDigest,
    MarketForecastSourceRecencyConsensusReasonCodeCount,
    MarketForecastSourceRecencyConsensusRow,
    MarketForecastSourceRecencyConsensusSource,
    build_market_forecast_source_recency_consensus_digest,
    market_forecast_source_recency_consensus_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


@dataclass(frozen=True)
class SuppliedSourceShape:
    market_slug: str
    forecast_id: str
    source_id: str
    source_family: str
    source_role: str
    source_observed_at: datetime | None
    forecast_probability: Decimal | None
    consensus_probability: Decimal | None
    source_weight: Decimal
    reference: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketForecastSourceRecencyConsensusConfig:
    values = {
        "config_version": "market-forecast-source-recency-consensus-digest-v0",
        "fresh_age_seconds": d("3600"),
        "stale_age_seconds": d("86400"),
        "min_independent_source_families": d("2"),
        "min_consensus_ratio": d("0.666667"),
        "max_probability_dispersion": d("0.150000"),
    }
    values.update(overrides)
    return MarketForecastSourceRecencyConsensusConfig(**values)


def source(
    index: int,
    *,
    market_slug: str = "btc-above-100k",
    forecast_id: str = "forecast-alpha",
    source_family: str = "official_resolution",
    source_role: str = "primary",
    source_observed_at: datetime | None = None,
    forecast_probability: Decimal | None = None,
    consensus_probability: Decimal | None = d("0.650000"),
    source_weight: Decimal = d("1.000000"),
    reference: str | None = None,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketForecastSourceRecencyConsensusSource:
    return MarketForecastSourceRecencyConsensusSource(
        market_slug=market_slug,
        forecast_id=forecast_id,
        source_id=f"source-{index:03d}",
        source_family=source_family,
        source_role=source_role,
        source_observed_at=(
            source_observed_at
            if source_observed_at is not None
            else GENERATED_AT - timedelta(minutes=15)
        ),
        forecast_probability=(
            forecast_probability if forecast_probability is not None else d("0.650000")
        ),
        consensus_probability=consensus_probability,
        source_weight=source_weight,
        reference=(
            reference
            if reference is not None
            else f"https://example.test/forecast/{index}?token=secret-value"
        ),
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    sources: tuple[object, ...],
    *,
    cfg: MarketForecastSourceRecencyConsensusConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketForecastSourceRecencyConsensusDigest:
    return build_market_forecast_source_recency_consensus_digest(
        sources,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_zero_digest() -> None:
    report = digest(())

    assert type(report) is MarketForecastSourceRecencyConsensusDigest
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-forecast-source-recency-consensus-digest-v0"
    assert report.market_count == d("0")
    assert report.source_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.stale_source_count == d("0")
    assert report.consensus_source_count == d("0")
    assert report.average_consensus_ratio is None
    assert report.average_probability_dispersion is None
    assert report.status == "blocked"
    assert report.reason_codes == ("no_forecast_sources",)
    assert report.rows == ()
    assert report.reason_code_counts == (
        MarketForecastSourceRecencyConsensusReasonCodeCount(
            reason_code="no_forecast_sources",
            count=d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_fresh_multi_family_consensus_passes_with_redacted_reference() -> None:
    report = digest(
        (
            source(
                2,
                source_family="model_signal",
                source_role="secondary",
                forecast_probability=d("0.660000"),
            ),
            source(
                1,
                source_family="official_resolution",
                source_role="primary",
                source_observed_at=datetime(
                    2026,
                    7,
                    2,
                    7,
                    45,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                forecast_probability=d("0.640000"),
                reference="https://source.example/path?api_key=super-secret",
            ),
        ),
    )

    assert report.status == "pass"
    assert report.reason_codes == ("forecast_source_recency_consensus_pass",)
    assert report.market_count == d("1")
    assert report.source_count == d("2")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.stale_source_count == d("0")
    assert report.consensus_source_count == d("2")
    assert report.average_consensus_ratio == d("1.000000")
    assert report.average_probability_dispersion == d("0.010000")

    row = report.rows[0]
    assert type(row) is MarketForecastSourceRecencyConsensusRow
    assert row.market_slug == "btc-above-100k"
    assert row.forecast_id == "forecast-alpha"
    assert row.source_count == d("2")
    assert row.independent_source_family_count == d("2")
    assert row.latest_source_observed_at == GENERATED_AT - timedelta(minutes=15)
    assert row.latest_source_age_seconds == d("900")
    assert row.stale_source_count == d("0")
    assert row.consensus_source_count == d("2")
    assert row.consensus_ratio == d("1.000000")
    assert row.average_forecast_probability == d("0.650000")
    assert row.consensus_probability == d("0.650000")
    assert row.probability_dispersion == d("0.010000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "forecast_sources_current",
        "forecast_sources_independent",
        "forecast_sources_in_consensus",
        "forecast_source_recency_consensus_pass",
    )
    assert row.source_ids == ("source-001", "source-002")
    assert row.source_families == ("model_signal", "official_resolution")
    assert row.redacted_references == ("[redacted_reference]",)


def test_stale_single_family_and_probability_dispersion_watch_market() -> None:
    report = digest(
        (
            source(
                1,
                source_family="model_signal",
                source_observed_at=GENERATED_AT - timedelta(days=2),
                forecast_probability=d("0.900000"),
                consensus_probability=d("0.650000"),
                reason_codes=("manual_review",),
            ),
            source(
                2,
                source_family="model_signal",
                source_observed_at=GENERATED_AT - timedelta(hours=12),
                forecast_probability=d("0.400000"),
                consensus_probability=d("0.650000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "watch"
    assert report.watch_count == d("1")
    assert report.stale_source_count == d("1")
    assert report.consensus_source_count == d("0")
    assert row.latest_source_age_seconds == d("43200")
    assert row.stale_source_count == d("1")
    assert row.independent_source_family_count == d("1")
    assert row.consensus_source_count == d("0")
    assert row.consensus_ratio == d("0.000000")
    assert row.average_forecast_probability == d("0.650000")
    assert row.probability_dispersion == d("0.250000")
    assert row.status == "watch"
    assert row.reason_codes == (
        "forecast_source_recency_consensus_watch",
        "forecast_sources_below_consensus",
        "forecast_sources_insufficient_independence",
        "forecast_sources_stale",
        "input_manual_review",
        "probability_dispersion_high",
    )
    assert report.reason_code_counts == (
        MarketForecastSourceRecencyConsensusReasonCodeCount(
            reason_code="forecast_source_recency_consensus_watch",
            count=d("1"),
        ),
        MarketForecastSourceRecencyConsensusReasonCodeCount(
            reason_code="forecast_sources_below_consensus",
            count=d("1"),
        ),
        MarketForecastSourceRecencyConsensusReasonCodeCount(
            reason_code="forecast_sources_insufficient_independence",
            count=d("1"),
        ),
        MarketForecastSourceRecencyConsensusReasonCodeCount(
            reason_code="forecast_sources_stale",
            count=d("1"),
        ),
        MarketForecastSourceRecencyConsensusReasonCodeCount(
            reason_code="input_manual_review",
            count=d("1"),
        ),
        MarketForecastSourceRecencyConsensusReasonCodeCount(
            reason_code="probability_dispersion_high",
            count=d("1"),
        ),
    )


def test_missing_source_payload_blocks_row() -> None:
    report = digest(
        (
            SuppliedSourceShape(
                market_slug="empty-market",
                forecast_id="forecast-empty",
                source_id="",
                source_family="",
                source_role="primary",
                source_observed_at=None,
                forecast_probability=None,
                consensus_probability=d("0.500000"),
                source_weight=d("0"),
                reference="",
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "blocked"
    assert row.market_slug == "empty-market"
    assert row.source_count == d("0")
    assert row.independent_source_family_count == d("0")
    assert row.latest_source_observed_at is None
    assert row.latest_source_age_seconds is None
    assert row.consensus_ratio == d("0.000000")
    assert row.average_forecast_probability is None
    assert row.probability_dispersion is None
    assert row.status == "blocked"
    assert row.reason_codes == ("missing_forecast_sources",)


def test_rows_and_reasons_sort_deterministically() -> None:
    report = digest(
        (
            source(
                3,
                market_slug="z-market",
                forecast_id="forecast-z",
                source_family="z-family",
                source_observed_at=GENERATED_AT - timedelta(days=2),
                forecast_probability=d("0.800000"),
                consensus_probability=d("0.600000"),
            ),
            source(
                1,
                market_slug="a-market",
                forecast_id="forecast-a",
                source_family="a-family",
                reason_codes=("zeta", "alpha"),
            ),
            source(
                2,
                market_slug="z-market",
                forecast_id="forecast-z",
                source_family="a-family",
                consensus_probability=d("0.600000"),
                reason_codes=("alpha",),
            ),
        ),
    )

    assert tuple(row.market_slug for row in report.rows) == ("a-market", "z-market")
    assert report.rows[0].reason_codes == (
        "forecast_source_recency_consensus_watch",
        "forecast_sources_current",
        "forecast_sources_in_consensus",
        "forecast_sources_insufficient_independence",
        "input_alpha",
        "input_zeta",
        "probability_dispersion_ok",
    )
    assert report.rows[1].source_ids == ("source-002", "source-003")
    assert report.reason_codes == (
        "forecast_source_recency_consensus_watch",
        "forecast_sources_below_consensus",
        "forecast_sources_current",
        "forecast_sources_in_consensus",
        "forecast_sources_insufficient_independence",
        "forecast_sources_stale",
        "input_alpha",
        "input_zeta",
        "probability_dispersion_high",
        "probability_dispersion_ok",
    )


def test_payload_uses_decimal_strings_utc_datetimes_and_no_float_or_sensitive_values() -> None:
    report = digest(
        (
            source(1),
            source(2, market_slug="z-market", forecast_id="forecast-z"),
        ),
        cfg=config(min_independent_source_families=d("1")),
    )

    payload = market_forecast_source_recency_consensus_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["market_count"] == "2"
    assert payload["average_consensus_ratio"] == "1.000000"
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["latest_source_age_seconds"] == "900"
    assert "2.0" not in encoded
    assert "secret" not in encoded.lower()
    assert "token" not in encoded.lower()
    assert "api_key" not in encoded.lower()
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_payload_rejects_raw_unsafe_surfaces_numeric_primitives_and_missing_flags() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        market_forecast_source_recency_consensus_digest_payload(
            {
                "report_only": True,
                "readonly": True,
            },
        )

    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        market_forecast_source_recency_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_count": 1,
            },
        )

    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        market_forecast_source_recency_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "average_consensus_ratio": 0.5,
            },
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        market_forecast_source_recency_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "generated_at": datetime(2026, 7, 2, 12, 0),
            },
        )

    with pytest.raises(ValueError, match="public payload values must be JSON-safe"):
        market_forecast_source_recency_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_count": d("1"),
            },
        )

    with pytest.raises(ValueError, match="public payload values must be JSON-safe"):
        market_forecast_source_recency_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "generated_at": GENERATED_AT,
            },
        )

    with pytest.raises(ValueError, match="public payload values must be JSON-safe"):
        market_forecast_source_recency_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": ({"market_slug": "btc-above-100k"},),
            },
        )

    with pytest.raises(ValueError, match="unsafe surface"):
        market_forecast_source_recency_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"market_slug": "wallet-risk"}],
            },
        )

    with pytest.raises(ValueError, match="unsafe surface"):
        market_forecast_source_recency_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "network_client": "disabled",
            },
        )


def test_validation_rejects_floats_nonfinite_decimals_datetimes_flags_and_reports() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("market-forecast-source-recency-consensus-digest-v0"))
    with pytest.raises(ValueError, match="fresh_age_seconds"):
        config(fresh_age_seconds=d("0"))
    with pytest.raises(ValueError, match="stale_age_seconds"):
        config(stale_age_seconds=d("3600"))
    with pytest.raises(ValueError, match="min_independent_source_families"):
        config(min_independent_source_families=2)
    with pytest.raises(ValueError, match="min_consensus_ratio"):
        config(min_consensus_ratio=0.5)
    with pytest.raises(ValueError, match="max_probability_dispersion"):
        config(max_probability_dispersion=_DecimalSubclass("0.150000"))
    with pytest.raises(ValueError, match="source_weight"):
        source(1, source_weight=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        digest((source(1),), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        digest((source(1),), generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="market_slug"):
        source(1, market_slug=" btc-above-100k")
    with pytest.raises(ValueError, match="forecast_probability"):
        source(1, forecast_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_observed_at"):
        source(1, source_observed_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="source_observed_at"):
        digest((source(1, source_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        source(1, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        source(1, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        source(1, readonly=False)

    report = digest((source(1),), cfg=config(min_independent_source_families=d("1")))
    with pytest.raises(ValueError, match="market_count"):
        replace(report, market_count=d("2"))
    with pytest.raises(ValueError, match="average_consensus_ratio"):
        replace(report, average_consensus_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")


def test_source_identity_fields_must_be_empty_or_canonical() -> None:
    with pytest.raises(ValueError, match="source_id"):
        MarketForecastSourceRecencyConsensusSource(
            market_slug="btc-above-100k",
            forecast_id="forecast-alpha",
            source_id=" source-001",
            source_family="official_resolution",
            source_role="primary",
            source_observed_at=GENERATED_AT - timedelta(minutes=15),
            forecast_probability=d("0.650000"),
            consensus_probability=d("0.650000"),
            source_weight=d("1.000000"),
            reference="https://example.test/forecast/1?token=secret-value",
        )
    with pytest.raises(ValueError, match="source_family"):
        MarketForecastSourceRecencyConsensusSource(
            market_slug="btc-above-100k",
            forecast_id="forecast-alpha",
            source_id="source-001",
            source_family="official_resolution ",
            source_role="primary",
            source_observed_at=GENERATED_AT - timedelta(minutes=15),
            forecast_probability=d("0.650000"),
            consensus_probability=d("0.650000"),
            source_weight=d("1.000000"),
            reference="https://example.test/forecast/1?token=secret-value",
        )


def test_public_count_fields_reject_fractional_decimal_counts() -> None:
    report = digest((source(1),), cfg=config(min_independent_source_families=d("1")))

    with pytest.raises(ValueError, match="source_count.*integer count"):
        replace(report.rows[0], source_count=d("1.5"))
    with pytest.raises(ValueError, match="market_count.*integer count"):
        replace(report, market_count=d("1.5"))
    with pytest.raises(ValueError, match="count.*integer count"):
        MarketForecastSourceRecencyConsensusReasonCodeCount(
            reason_code="forecast_source_recency_consensus_pass",
            count=d("1.5"),
        )


def test_public_dataclasses_are_frozen() -> None:
    report = digest((source(1),), cfg=config(min_independent_source_families=d("1")))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]


def test_public_dataclasses_reject_tampered_derived_invariants() -> None:
    report = digest((source(1),), cfg=config(min_independent_source_families=d("1")))
    row = report.rows[0]

    with pytest.raises(ValueError, match="consensus_ratio"):
        replace(row, consensus_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            report,
            reason_code_counts=(
                MarketForecastSourceRecencyConsensusReasonCodeCount(
                    reason_code="forecast_source_recency_consensus_pass",
                    count=d("2"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_derived_validation_digest_is_stable_sha256_hex() -> None:
    first = digest((source(1),), cfg=config(min_independent_source_families=d("1")))
    second = digest((source(1),), cfg=config(min_independent_source_families=d("1")))
    changed = digest(
        (
            source(
                1,
                forecast_probability=d("0.600000"),
            ),
        ),
        cfg=config(min_independent_source_families=d("1")),
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.derived_validation_digest != changed.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)


def test_static_forbidden_surface_terms_are_absent_from_owned_module() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_forecast_source_recency_consensus_digest.py"
    )
    source_text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "psycopg",
        "postgres",
        "supabase",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "wallet",
        "broker",
        "order",
        "signing",
        "auth",
        "live",
        "trade",
        "network",
        "database",
        "persist",
        "advice",
        "open(",
    )

    assert all(term not in source_text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
