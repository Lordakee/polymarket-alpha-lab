from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_jolts_surprise_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    digest = api()
    values = {
        "fresh_release_max_age_seconds": d("7200.000000"),
        "min_source_count": d("2"),
        "material_surprise_threshold_jobs": d("250000.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchJoltsSurpriseDigestConfig(**values)


def input_row(
    research_key: str = "research.jolts.headline",
    *,
    condition_id: str = "condition_jolts_openings",
    market_slug: str = "jolts-job-openings-above-consensus",
    jolts_report_key: str = "bls.jolts.openings",
    jolts_report_family: str = "job_openings",
    jolts_report_reference: str = "public-bls-jolts-calendar",
    released_at: datetime | None = None,
    acknowledged_at: object = None,
    source_count: Decimal = d("2"),
    forecast_openings_count: Decimal = d("7600000.000000"),
    actual_openings_count: Decimal = d("7750000.000000"),
    surprise_score: Decimal = d("0.020000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = api()
    return digest.MarketResearchJoltsSurpriseDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        jolts_report_key=jolts_report_key,
        jolts_report_family=jolts_report_family,
        jolts_report_reference=jolts_report_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=30),
        acknowledged_at=acknowledged_at,
        source_count=source_count,
        forecast_openings_count=forecast_openings_count,
        actual_openings_count=actual_openings_count,
        surprise_score=surprise_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows, generated_at: datetime = GENERATED_AT):
    digest = api()
    return digest.build_market_research_jolts_surprise_digest(
        rows,
        config=config(),
        generated_at=generated_at,
    )


def test_jolts_surprise_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    digest_report = report(
        input_row(
            "research.jolts.quit_rate",
            condition_id="condition_jolts_quits",
            market_slug="jolts-quits-rate-cools",
            jolts_report_key="bls.jolts.quits",
            jolts_report_family="quits",
            jolts_report_reference="private-labor-feed",
            released_at=GENERATED_AT - timedelta(hours=4),
            acknowledged_at=None,
            source_count=d("2"),
            forecast_openings_count=d("3900000.000000"),
            actual_openings_count=d("3500000.000000"),
            surprise_score=d("0.100000"),
        ),
        input_row(
            "research.jolts.headline",
            condition_id="condition_jolts_openings",
            market_slug="jolts-job-openings-above-consensus",
            jolts_report_key="bls.jolts.openings",
            jolts_report_family="openings",
            jolts_report_reference="https://vendor.example/jolts?token=secret-123",
            released_at=GENERATED_AT - timedelta(hours=3),
            acknowledged_at=GENERATED_AT - timedelta(minutes=70),
            source_count=d("1"),
            forecast_openings_count=d("7600000.000000"),
            actual_openings_count=d("7950000.000000"),
            surprise_score=d("0.050000"),
        ),
        input_row(
            "research.jolts.hires",
            condition_id="condition_jolts_hires",
            market_slug="jolts-hires-inline",
            jolts_report_key="bls.jolts.hires",
            jolts_report_family="hires",
            jolts_report_reference="public-bls-jolts-calendar",
            released_at=GENERATED_AT - timedelta(minutes=40),
            acknowledged_at=GENERATED_AT - timedelta(minutes=35),
            source_count=d("3"),
            forecast_openings_count=d("5700000.000000"),
            actual_openings_count=d("5780000.000000"),
            surprise_score=d("0.015000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == "market-research-jolts-surprise-digest-v0"
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_jolts_surprise_digest"
    )
    assert digest_report.jolts_report_count == d("3.000000")
    assert digest_report.ready_report_count == d("1.000000")
    assert digest_report.watch_report_count == d("1.000000")
    assert digest_report.blocked_report_count == d("1.000000")
    assert digest_report.material_surprise_count == d("2.000000")
    assert digest_report.stale_release_count == d("2.000000")
    assert digest_report.thin_source_count == d("1.000000")
    assert digest_report.missing_acknowledgement_count == d("1.000000")
    assert digest_report.slow_acknowledgement_count == d("1.000000")
    assert digest_report.average_surprise_score == d("0.055000")
    assert digest_report.max_release_age_seconds == d("14400.000000")
    assert digest_report.average_source_count == d("2.000000")
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.market_slug for row in digest_report.rows) == (
        "jolts-quits-rate-cools",
        "jolts-job-openings-above-consensus",
        "jolts-hires-inline",
    )

    blocked = digest_report.rows[0]
    assert blocked.surprise_status == "blocked"
    assert blocked.release_age_seconds == d("14400.000000")
    assert blocked.acknowledgement_lag_seconds is None
    assert blocked.jolts_surprise_jobs == d("-400000.000000")
    assert blocked.redacted_jolts_report_reference == "sha256:dcd9eea73513"
    assert blocked.reason_codes == (
        "market_research_jolts_surprise_digest_material_surprise",
        "market_research_jolts_surprise_digest_missing_acknowledgement",
        "market_research_jolts_surprise_digest_stale_release",
    )

    watch = digest_report.rows[1]
    assert watch.surprise_status == "watch"
    assert watch.release_age_seconds == d("10800.000000")
    assert watch.acknowledgement_lag_seconds == d("6600.000000")
    assert watch.jolts_surprise_jobs == d("350000.000000")
    assert watch.redacted_jolts_report_reference == "sha256:9bd473a11678"
    assert watch.reason_codes == (
        "market_research_jolts_surprise_digest_material_surprise",
        "market_research_jolts_surprise_digest_slow_acknowledgement",
        "market_research_jolts_surprise_digest_stale_release",
        "market_research_jolts_surprise_digest_thin_sources",
    )

    ready = digest_report.rows[2]
    assert ready.surprise_status == "ready"
    assert ready.release_age_seconds == d("2400.000000")
    assert ready.acknowledgement_lag_seconds == d("300.000000")
    assert ready.jolts_surprise_jobs == d("80000.000000")
    assert ready.redacted_jolts_report_reference == "public-bls-jolts-calendar"
    assert ready.reason_codes == ("market_research_jolts_surprise_digest_ready",)

    assert tuple(item.reason_code for item in digest_report.reason_code_counts) == (
        "market_research_jolts_surprise_digest_material_surprise",
        "market_research_jolts_surprise_digest_stale_release",
        "market_research_jolts_surprise_digest_missing_acknowledgement",
        "market_research_jolts_surprise_digest_ready",
        "market_research_jolts_surprise_digest_slow_acknowledgement",
        "market_research_jolts_surprise_digest_thin_sources",
    )
    assert tuple(item.count for item in digest_report.reason_code_counts) == (
        d("2.000000"),
        d("2.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
    )
    assert tuple(item.report_ratio for item in digest_report.reason_code_counts) == (
        d("0.666667"),
        d("0.666667"),
        d("0.333333"),
        d("0.333333"),
        d("0.333333"),
        d("0.333333"),
    )
    assert digest_report.reason_codes == tuple(
        item.reason_code for item in digest_report.reason_code_counts
    )

    serialized = repr(asdict(digest_report)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "private-labor-feed",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "token",
    ):
        assert token not in serialized


def test_empty_jolts_surprise_digest_is_blocked_and_decimal_zeroed() -> None:
    digest = api()
    digest_report = report()

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_jolts_surprise_digest"
    )
    assert digest_report.jolts_report_count == ZERO
    assert digest_report.ready_report_count == ZERO
    assert digest_report.watch_report_count == ZERO
    assert digest_report.blocked_report_count == ZERO
    assert digest_report.average_surprise_score == ZERO
    assert digest_report.max_release_age_seconds == ZERO
    assert digest_report.average_source_count == ZERO
    assert digest_report.rows == ()
    assert digest_report.reason_code_counts == (
            digest.MarketResearchJoltsSurpriseDigestReasonCodeCount(
                reason_code="market_research_jolts_surprise_digest_no_inputs",
                count=d("1.000000"),
                report_ratio=ZERO,
            ),
    )
    assert digest_report.reason_codes == (
        "market_research_jolts_surprise_digest_no_inputs",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_payload_decimal_strings_and_public_surface_decimal_only() -> None:
    digest = api()
    digest_report = report(input_row())
    payload = digest.market_research_jolts_surprise_digest_payload(digest_report)

    assert payload["jolts_report_count"] == "1.000000"
    assert payload["average_surprise_score"] == "0.020000"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'jolts_report_reference':" not in repr(payload)

    for value in (
        config(),
        input_row(),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert_decimal_numeric_fields(value)


def test_validates_frozen_types_dates_flags_and_consistency() -> None:
    digest = api()

    assert is_dataclass(digest.MarketResearchJoltsSurpriseDigestConfig)
    assert is_dataclass(digest.MarketResearchJoltsSurpriseDigestInputRow)
    assert is_dataclass(digest.MarketResearchJoltsSurpriseDigestRow)
    assert is_dataclass(digest.MarketResearchJoltsSurpriseDigestReasonCodeCount)
    assert is_dataclass(digest.MarketResearchJoltsSurpriseDigestReport)

    for public_dataclass in (
        digest.MarketResearchJoltsSurpriseDigestConfig,
        digest.MarketResearchJoltsSurpriseDigestInputRow,
        digest.MarketResearchJoltsSurpriseDigestRow,
        digest.MarketResearchJoltsSurpriseDigestReasonCodeCount,
        digest.MarketResearchJoltsSurpriseDigestReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Unsafe{public_dataclass.__name__}", (public_dataclass,), {})

    digest_report = report(input_row())
    ready = digest_report.rows[0]
    reason_count = digest_report.reason_code_counts[0]
    with pytest.raises(FrozenInstanceError):
        ready.source_count = d("3.000000")  # type: ignore[misc]

    false_flag_cases = (
        ("config paper_only", lambda: config(paper_only=False)),
        ("config report_only", lambda: config(report_only=False)),
        ("config readonly", lambda: config(readonly=False)),
        ("input row paper_only", lambda: input_row(paper_only=False)),
        ("input row report_only", lambda: input_row(report_only=False)),
        ("input row readonly", lambda: input_row(readonly=False)),
        ("row paper_only", lambda: replace(ready, paper_only=False)),
        ("row report_only", lambda: replace(ready, report_only=False)),
        ("row readonly", lambda: replace(ready, readonly=False)),
        ("reason count paper_only", lambda: replace(reason_count, paper_only=False)),
        ("reason count report_only", lambda: replace(reason_count, report_only=False)),
        ("reason count readonly", lambda: replace(reason_count, readonly=False)),
        ("report paper_only", lambda: replace(digest_report, paper_only=False)),
        ("report report_only", lambda: replace(digest_report, report_only=False)),
        ("report readonly", lambda: replace(digest_report, readonly=False)),
    )
    for expected_error, make_bad_record in false_flag_cases:
        with pytest.raises(ValueError, match=expected_error):
            make_bad_record()

    with pytest.raises(ValueError, match="forecast_openings_count must be a Decimal"):
        input_row(forecast_openings_count=7600000)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="actual_openings_count must be a Decimal"):
        input_row(actual_openings_count=7950000.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="released_at must be timezone-aware"):
        input_row(released_at=datetime(2026, 7, 3, 13, 0))
    with pytest.raises(ValueError, match="released_at must be timezone-aware"):
        input_row(released_at=datetime(2026, 7, 3, 13, 0, tzinfo=NoneOffsetTZ()))
    with pytest.raises(ValueError, match="released_at must be a datetime"):
        input_row(released_at=DateTimeSubclass(2026, 7, 3, 13, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="acknowledged_at cannot be before released_at"):
        report(
            input_row(
                released_at=GENERATED_AT - timedelta(minutes=10),
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
            ),
        )
    with pytest.raises(ValueError, match="input rows must use unique"):
        report(input_row(), input_row())
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_jolts_surprise_digest_ready",
                "market_research_jolts_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="count"):
        digest.MarketResearchJoltsSurpriseDigestReasonCodeCount(
            reason_code="market_research_jolts_surprise_digest_no_inputs",
            count=ZERO,
            report_ratio=ZERO,
        )
    multi_reason_report = report(
        input_row(
            "research.jolts.multi",
            jolts_report_key="bls.jolts.multi",
            released_at=GENERATED_AT - timedelta(hours=3),
            acknowledged_at=None,
            forecast_openings_count=d("7600000.000000"),
            actual_openings_count=d("8000000.000000"),
            surprise_score=d("0.100000"),
        ),
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            multi_reason_report,
            reason_code_counts=tuple(reversed(multi_reason_report.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            multi_reason_report,
            reason_codes=tuple(reversed(multi_reason_report.reason_codes)),
        )
    with pytest.raises(ValueError, match="jolts_surprise_jobs"):
        replace(ready, jolts_surprise_jobs=d("1.000000"))
    with pytest.raises(ValueError, match="release_age_seconds"):
        replace(
            digest_report,
            rows=(replace(ready, release_age_seconds=d("1.000000")),),
        )


def test_jolts_surprise_digest_sorting_uses_stable_public_tie_breakers() -> None:
    later_research = input_row(
        "research.jolts.zeta",
        condition_id="condition_jolts_zeta",
        market_slug="jolts-same-slug",
        jolts_report_key="bls.jolts.tie",
        released_at=GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=GENERATED_AT - timedelta(minutes=10),
        surprise_score=d("0.010000"),
    )
    earlier_research = input_row(
        "research.jolts.alpha",
        condition_id="condition_jolts_alpha",
        market_slug="jolts-same-slug",
        jolts_report_key="bls.jolts.tie",
        released_at=GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=GENERATED_AT - timedelta(minutes=10),
        surprise_score=d("0.010000"),
    )

    digest_report = report(later_research, earlier_research)

    assert tuple(row.research_key for row in digest_report.rows) == (
        "research.jolts.alpha",
        "research.jolts.zeta",
    )


def test_module_has_no_network_durable_store_or_trading_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_jolts_surprise_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "open(",
        "wallet",
        "private_key",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
        "auth",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name.split(".")[0] for alias in node.names}
            assert names.isdisjoint({"requests", "httpx", "aiohttp", "socket", "sqlite3"})
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in {
                "requests",
                "httpx",
                "aiohttp",
                "socket",
                "sqlite3",
            }


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_score")
            or field.name.endswith("_seconds")
            or field.name.endswith("_jobs")
            or field.name.endswith("_threshold_jobs")
        ):
            field_value = getattr(value, field.name)
            if field_value is None:
                continue
            assert type(field_value) is Decimal, field.name


def test_payload_revalidates_nested_public_report_tree_before_serializing() -> None:
    digest = api()
    digest_report = report(input_row())

    object.__setattr__(digest_report.rows[0], "paper_only", False)

    with pytest.raises(ValueError, match="row paper_only must be True"):
        digest.market_research_jolts_surprise_digest_payload(digest_report)


class NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


class DateTimeSubclass(datetime):
    pass
