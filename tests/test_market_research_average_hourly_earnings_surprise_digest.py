from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.market_research_average_hourly_earnings_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_AVERAGE_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchAverageHourlyEarningsSurpriseDigestConfig,
    MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount,
    MarketResearchAverageHourlyEarningsSurpriseDigestReport,
    MarketResearchAverageHourlyEarningsSurpriseDigestRow,
    MarketResearchAverageHourlyEarningsSurpriseDigestSignal,
    build_market_research_average_hourly_earnings_surprise_digest,
    market_research_average_hourly_earnings_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "missing-offset"


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchAverageHourlyEarningsSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_AVERAGE_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("3600.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_ratio": d("0.200000"),
        "max_prior_revision_ratio": d("0.500000"),
        "min_confirmation_ratio": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchAverageHourlyEarningsSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_ahe_hot",
    *,
    market_slug: str = "average-hourly-earnings-hot-print",
    release_id: str = "employment.average_hourly_earnings.june",
    series_id: str = "ces.average_hourly_earnings.private",
    public_signal_reference: str = "official-bls-ahe-release",
    observed_at: datetime | None = None,
    expected_average_hourly_earnings_growth: Decimal = d("0.003000"),
    actual_average_hourly_earnings_growth: Decimal = d("0.004000"),
    prior_average_hourly_earnings_growth: Decimal = d("0.004000"),
    source_count: Decimal = d("3.000000"),
    confirmation_ratio: Decimal = d("0.900000"),
    signal_config_version: str = "average-hourly-earnings-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchAverageHourlyEarningsSurpriseDigestSignal:
    return MarketResearchAverageHourlyEarningsSurpriseDigestSignal(
        condition_id=condition_id,
        market_slug=market_slug,
        release_id=release_id,
        series_id=series_id,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        expected_average_hourly_earnings_growth=expected_average_hourly_earnings_growth,
        actual_average_hourly_earnings_growth=actual_average_hourly_earnings_growth,
        prior_average_hourly_earnings_growth=prior_average_hourly_earnings_growth,
        source_count=source_count,
        confirmation_ratio=confirmation_ratio,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[MarketResearchAverageHourlyEarningsSurpriseDigestSignal, ...],
    *,
    cfg: MarketResearchAverageHourlyEarningsSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchAverageHourlyEarningsSurpriseDigestReport:
    return build_market_research_average_hourly_earnings_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_average_hourly_earnings_digest_reduces_and_sorts_deterministically() -> None:
    summary = report(
        (
            signal(
                "condition_ahe_ready",
                market_slug="average-hourly-earnings-inline-print",
                release_id="employment.average_hourly_earnings.inline",
                observed_at=GENERATED_AT - timedelta(minutes=10),
                actual_average_hourly_earnings_growth=d("0.003000"),
                prior_average_hourly_earnings_growth=d("0.003000"),
                public_signal_reference="public-ahe-inline",
            ),
            signal(
                "condition_ahe_stale",
                market_slug="average-hourly-earnings-stale-hot",
                release_id="employment.average_hourly_earnings.stale",
                observed_at=GENERATED_AT - timedelta(hours=2),
                actual_average_hourly_earnings_growth=d("0.005000"),
                prior_average_hourly_earnings_growth=d("0.005000"),
                source_count=d("1.000000"),
                public_signal_reference="https://example.test/ahe?token=secret",
            ),
            signal(
                "condition_ahe_watch",
                market_slug="average-hourly-earnings-watch-hot",
                release_id="employment.average_hourly_earnings.watch",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_AVERAGE_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_average_hourly_earnings_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.missing_evidence_count == d("1.000000")
    assert summary.high_revision_count == ZERO
    assert summary.confirmation_gap_count == ZERO
    assert summary.average_absolute_surprise_ratio == d("0.333333")
    assert summary.max_absolute_surprise_ratio == d("0.666667")
    assert summary.average_source_count == d("2.333333")
    assert summary.max_observed_signal_age_seconds == d("7200.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.release_id for row in summary.rows) == (
        "employment.average_hourly_earnings.stale",
        "employment.average_hourly_earnings.watch",
        "employment.average_hourly_earnings.inline",
    )

    stale = summary.rows[0]
    assert stale.digest_status == "blocked"
    assert stale.signal_age_seconds == d("7200.000000")
    assert stale.average_hourly_earnings_surprise_delta == d("0.002000")
    assert stale.average_hourly_earnings_surprise_ratio == d("0.666667")
    assert stale.absolute_surprise_ratio == d("0.666667")
    assert stale.prior_revision_delta == ZERO
    assert stale.prior_revision_ratio == ZERO
    assert stale.redacted_public_signal_reference.startswith("sha256:")
    assert stale.reason_codes == (
        "market_research_average_hourly_earnings_surprise_digest_stale_signal",
        "market_research_average_hourly_earnings_surprise_digest_missing_evidence",
        "market_research_average_hourly_earnings_surprise_digest_material_surprise",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.signal_age_seconds == d("1800.000000")
    assert watch.average_hourly_earnings_surprise_delta == d("0.001000")
    assert watch.average_hourly_earnings_surprise_ratio == d("0.333333")
    assert watch.reason_codes == (
        "market_research_average_hourly_earnings_surprise_digest_material_surprise",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.average_hourly_earnings_surprise_delta == ZERO
    assert ready.average_hourly_earnings_surprise_ratio == ZERO
    assert ready.redacted_public_signal_reference == "public-ahe-inline"
    assert ready.reason_codes == (
        "market_research_average_hourly_earnings_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_average_hourly_earnings_surprise_digest_missing_evidence"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_average_hourly_earnings_surprise_digest_material_surprise"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount(
            reason_code="market_research_average_hourly_earnings_surprise_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount(
            reason_code="market_research_average_hourly_earnings_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_average_hourly_earnings_surprise_digest_missing_evidence",
        "market_research_average_hourly_earnings_surprise_digest_material_surprise",
        "market_research_average_hourly_earnings_surprise_digest_stale_signal",
        "market_research_average_hourly_earnings_surprise_digest_ready",
    )


def test_empty_average_hourly_earnings_digest_blocks_with_no_inputs_evidence() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_average_hourly_earnings_surprise_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.material_surprise_count == ZERO
    assert summary.stale_signal_count == ZERO
    assert summary.missing_evidence_count == ZERO
    assert summary.high_revision_count == ZERO
    assert summary.confirmation_gap_count == ZERO
    assert summary.average_absolute_surprise_ratio == ZERO
    assert summary.max_absolute_surprise_ratio == ZERO
    assert summary.average_source_count == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount(
            reason_code="market_research_average_hourly_earnings_surprise_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_average_hourly_earnings_surprise_digest_no_inputs",
    )


def test_payload_uses_six_decimal_strings_utc_datetimes_and_no_floats() -> None:
    summary = report(
        (
            signal(
                public_signal_reference="public-ahe-token-secret-reference",
            ),
        ),
    )
    payload = market_research_average_hourly_earnings_surprise_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T15:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["average_absolute_surprise_ratio"] == "0.333333"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T14:30:00+00:00"
    assert payload["rows"][0]["average_hourly_earnings_surprise_delta"] == "0.001000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["reason_code_counts"][0]["signal_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert summary.rows[0].redacted_public_signal_reference.startswith("sha256:")
    assert "public-ahe-token-secret-reference" not in repr(payload)
    assert "token" not in repr(payload).lower()
    assert "secret" not in repr(payload).lower()

    with pytest.raises(
        ValueError,
        match="MarketResearchAverageHourlyEarningsSurpriseDigestReport",
    ):
        market_research_average_hourly_earnings_surprise_digest_payload(payload)  # type: ignore[arg-type]


def test_public_dataclasses_are_frozen_exact_type_and_decimal_only() -> None:
    summary = report((signal(),))

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].market_slug = "changed"  # type: ignore[misc]

    public_numeric_names = {
        "actual_average_hourly_earnings_growth",
        "average_absolute_surprise_ratio",
        "average_hourly_earnings_surprise_delta",
        "average_hourly_earnings_surprise_ratio",
        "average_source_count",
        "absolute_surprise_ratio",
        "blocked_signal_count",
        "confirmation_gap_count",
        "confirmation_ratio",
        "count",
        "expected_average_hourly_earnings_growth",
        "high_revision_count",
        "material_surprise_count",
        "material_surprise_ratio",
        "max_absolute_surprise_ratio",
        "max_observed_signal_age_seconds",
        "max_prior_revision_ratio",
        "max_signal_age_seconds",
        "min_confirmation_ratio",
        "min_source_count",
        "missing_evidence_count",
        "prior_average_hourly_earnings_growth",
        "prior_revision_delta",
        "prior_revision_ratio",
        "ready_signal_count",
        "signal_age_seconds",
        "signal_count",
        "signal_ratio",
        "source_count",
        "stale_signal_count",
        "watch_signal_count",
    }
    for cls in (
        MarketResearchAverageHourlyEarningsSurpriseDigestConfig,
        MarketResearchAverageHourlyEarningsSurpriseDigestSignal,
        MarketResearchAverageHourlyEarningsSurpriseDigestRow,
        MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount,
        MarketResearchAverageHourlyEarningsSurpriseDigestReport,
    ):
        type_hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in public_numeric_names:
                assert type_hints[field.name] is Decimal

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadConfig(MarketResearchAverageHourlyEarningsSurpriseDigestConfig):
            pass

    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 3, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 15, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 15, 0, tzinfo=_MissingOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report((), generated_at=datetime(2026, 7, 3, 15, 0, tzinfo=_MissingOffsetTimezone()))
    with pytest.raises(ValueError, match="expected_average_hourly_earnings_growth"):
        signal(expected_average_hourly_earnings_growth=0.003)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_count"):
        signal(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="confirmation_ratio"):
        signal(confirmation_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="condition_id"):
        signal(condition_id=_StringSubclass("condition_ahe"))
    with pytest.raises(ValueError, match="actual_average_hourly_earnings_growth"):
        signal(actual_average_hourly_earnings_growth=_DecimalSubclass("0.004000"))
    with pytest.raises(ValueError, match="unique condition_id"):
        report((signal("condition_duplicate"), signal("condition_duplicate")))


def test_public_dataclasses_reject_explicit_false_phase_flags() -> None:
    summary = report((signal(),))

    with pytest.raises(ValueError, match="config.report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="signal.paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="row.readonly"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason_code_count.paper_only"):
        replace(summary.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report.report_only"):
        replace(summary, report_only=False)


def test_public_constructors_reject_noncanonical_rows_reasons_and_counts() -> None:
    summary = report(
        (
            signal(
                "condition_ahe_stale",
                release_id="employment.average_hourly_earnings.stale",
                observed_at=GENERATED_AT - timedelta(hours=2),
                actual_average_hourly_earnings_growth=d("0.005000"),
                prior_average_hourly_earnings_growth=d("0.005000"),
                source_count=d("1.000000"),
            ),
            signal("condition_ahe_watch", release_id="employment.average_hourly_earnings.watch"),
            signal(
                "condition_ahe_ready",
                release_id="employment.average_hourly_earnings.ready",
                observed_at=GENERATED_AT - timedelta(minutes=10),
                actual_average_hourly_earnings_growth=d("0.003000"),
                prior_average_hourly_earnings_growth=d("0.003000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary.rows[0], reason_codes=tuple(reversed(summary.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=tuple(reversed(summary.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=tuple(reversed(summary.reason_codes)))

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            summary,
            reason_code_counts=(
                MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount(
                    reason_code=(
                        "market_research_average_hourly_earnings_surprise_digest_no_inputs"
                    ),
                    count=d("1.000000"),
                    signal_ratio=ZERO,
                ),
            ),
        )
    with pytest.raises(ValueError, match="count"):
        MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount(
            reason_code="market_research_average_hourly_earnings_surprise_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )


def test_module_is_pure_phase1_report_only_without_io_or_trading_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_average_hourly_earnings_surprise_digest",
    )
    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_AVERAGE_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION",
        "MarketResearchAverageHourlyEarningsSurpriseDigestConfig",
        "MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount",
        "MarketResearchAverageHourlyEarningsSurpriseDigestReport",
        "MarketResearchAverageHourlyEarningsSurpriseDigestRow",
        "MarketResearchAverageHourlyEarningsSurpriseDigestSignal",
        "build_market_research_average_hourly_earnings_surprise_digest",
        "market_research_average_hourly_earnings_surprise_digest_payload",
    )
    source = getattr(module, "__loader__").get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins.open",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "fetch",
        "get",
        "open",
        "post",
        "put",
        "read",
        "request",
        "submit",
        "write",
    }
    forbidden_name_fragments = (
        "account",
        "broker",
        "cancel",
        "exchange",
        "private_key",
        "trade",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_call_names
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_call_names
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
        if isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
    assert "private_key" not in source.lower()
    assert "database" not in source.lower()


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for key, item in value.items():
            items.append(key)
            items.extend(_walk_payload_values(item))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(_walk_payload_values(item))
        return tuple(items)
    return (value,)
