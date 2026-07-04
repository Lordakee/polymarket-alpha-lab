from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_nonfarm_payroll_revision_digest import (
    DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLL_REVISION_DIGEST_CONFIG_VERSION,
    MarketResearchNonfarmPayrollRevisionDigestConfig,
    MarketResearchNonfarmPayrollRevisionDigestInputRow,
    MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount,
    MarketResearchNonfarmPayrollRevisionDigestReport,
    MarketResearchNonfarmPayrollRevisionDigestRow,
    build_market_research_nonfarm_payroll_revision_digest,
    market_research_nonfarm_payroll_revision_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchNonfarmPayrollRevisionDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLL_REVISION_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("7200.000000"),
        "material_revision_threshold_jobs": d("50000"),
        "min_source_count": d("2"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchNonfarmPayrollRevisionDigestConfig(**values)


def input_row(
    research_key: str = "research.nfp.bls",
    *,
    condition_id: str = "condition_nfp_revision",
    payroll_series_key: str = "ces.total_nonfarm_payrolls",
    release_reference: str = "public-bls-employment-situation",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3"),
    previous_payroll_jobs: Decimal = d("150000"),
    revised_payroll_jobs: Decimal = d("185000"),
    consensus_payroll_jobs: Decimal = d("170000"),
    unemployment_rate: Decimal = d("0.041000"),
    labor_force_participation_rate: Decimal = d("0.626000"),
    market_probability_before: Decimal = d("0.460000"),
    market_probability_after: Decimal = d("0.500000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchNonfarmPayrollRevisionDigestInputRow:
    return MarketResearchNonfarmPayrollRevisionDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        payroll_series_key=payroll_series_key,
        release_reference=release_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=45),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=30)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        previous_payroll_jobs=previous_payroll_jobs,
        revised_payroll_jobs=revised_payroll_jobs,
        consensus_payroll_jobs=consensus_payroll_jobs,
        unemployment_rate=unemployment_rate,
        labor_force_participation_rate=labor_force_participation_rate,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchNonfarmPayrollRevisionDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchNonfarmPayrollRevisionDigestReport:
    return build_market_research_nonfarm_payroll_revision_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_nonfarm_payroll_revision_digest_reduces_rows_redacts_refs_and_sorts_deterministically() -> None:
    summary = report(
        (
            input_row(
                "research.nfp.private",
                condition_id="condition_private_jobs",
                payroll_series_key="adp.private_nonfarm_payrolls",
                release_reference="private-payroll-feed",
                released_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=None,
                source_count=d("2"),
                previous_payroll_jobs=d("110000"),
                revised_payroll_jobs=d("185000"),
                consensus_payroll_jobs=d("130000"),
                unemployment_rate=d("0.042000"),
                labor_force_participation_rate=d("0.625000"),
                market_probability_before=d("0.300000"),
                market_probability_after=d("0.360000"),
            ),
            input_row(
                "research.nfp.regional",
                condition_id="condition_regional_jobs",
                payroll_series_key="regional.nonfarm_payrolls",
                release_reference="https://vendor.example/payrolls?feed=regional",
                released_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=70),
                source_count=d("1"),
                previous_payroll_jobs=d("90000"),
                revised_payroll_jobs=d("145000"),
                consensus_payroll_jobs=d("100000"),
                unemployment_rate=d("0.039000"),
                labor_force_participation_rate=d("0.627000"),
                market_probability_before=d("0.410000"),
                market_probability_after=d("0.550000"),
            ),
            input_row(
                "research.nfp.bls",
                condition_id="condition_nfp_revision",
                payroll_series_key="ces.total_nonfarm_payrolls",
                release_reference="public-bls-employment-situation",
                released_at=GENERATED_AT - timedelta(minutes=45),
                acknowledged_at=GENERATED_AT - timedelta(minutes=35),
                source_count=d("3"),
                previous_payroll_jobs=d("150000"),
                revised_payroll_jobs=d("185000"),
                consensus_payroll_jobs=d("170000"),
                unemployment_rate=d("0.041000"),
                labor_force_participation_rate=d("0.626000"),
                market_probability_before=d("0.460000"),
                market_probability_after=d("0.500000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLL_REVISION_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_nonfarm_payroll_revision_digest"
    )
    assert summary.release_count == d("3.000000")
    assert summary.ready_release_count == d("1.000000")
    assert summary.watch_release_count == d("1.000000")
    assert summary.blocked_release_count == d("1.000000")
    assert summary.material_revision_count == d("2.000000")
    assert summary.stale_release_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.probability_repricing_count == d("1.000000")
    assert summary.average_revision_abs_jobs == d("55000.000000")
    assert summary.max_release_age_seconds == d("18000.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.payroll_series_key, row.research_key) for row in summary.rows) == (
        ("adp.private_nonfarm_payrolls", "research.nfp.private"),
        ("regional.nonfarm_payrolls", "research.nfp.regional"),
        ("ces.total_nonfarm_payrolls", "research.nfp.bls"),
    )

    private = summary.rows[0]
    assert private.revision_status == "blocked"
    assert private.release_age_seconds == d("18000.000000")
    assert private.acknowledgement_lag_seconds is None
    assert private.revision_delta_jobs == d("75000.000000")
    assert private.revision_abs_jobs == d("75000.000000")
    assert private.consensus_delta_jobs == d("55000.000000")
    assert private.probability_delta == d("0.060000")
    assert private.redacted_release_reference == "sha256:5da95395a13e"
    assert private.reason_codes == (
        "market_research_nonfarm_payroll_revision_digest_material_revision",
        "market_research_nonfarm_payroll_revision_digest_missing_acknowledgement",
        "market_research_nonfarm_payroll_revision_digest_stale_release",
    )

    regional = summary.rows[1]
    assert regional.revision_status == "watch"
    assert regional.release_age_seconds == d("10800.000000")
    assert regional.acknowledgement_lag_seconds == d("6600.000000")
    assert regional.revision_delta_jobs == d("55000.000000")
    assert regional.probability_delta == d("0.140000")
    assert regional.redacted_release_reference == "sha256:0a6be11d91e4"
    assert regional.reason_codes == (
        "market_research_nonfarm_payroll_revision_digest_material_revision",
        "market_research_nonfarm_payroll_revision_digest_probability_repricing",
        "market_research_nonfarm_payroll_revision_digest_slow_acknowledgement",
        "market_research_nonfarm_payroll_revision_digest_stale_release",
        "market_research_nonfarm_payroll_revision_digest_thin_sources",
    )

    bls = summary.rows[2]
    assert bls.revision_status == "ready"
    assert bls.release_age_seconds == d("2700.000000")
    assert bls.acknowledgement_lag_seconds == d("600.000000")
    assert bls.revision_delta_jobs == d("35000.000000")
    assert bls.revision_abs_jobs == d("35000.000000")
    assert bls.consensus_delta_jobs == d("15000.000000")
    assert bls.probability_delta == d("0.040000")
    assert bls.redacted_release_reference == "public-bls-employment-situation"
    assert bls.reason_codes == (
        "market_research_nonfarm_payroll_revision_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payroll_revision_digest_material_revision",
            count=d("2.000000"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payroll_revision_digest_stale_release",
            count=d("2.000000"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_nonfarm_payroll_revision_digest_probability_repricing"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_nonfarm_payroll_revision_digest_missing_acknowledgement"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payroll_revision_digest_slow_acknowledgement",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payroll_revision_digest_thin_sources",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
    )


def test_nonfarm_payroll_revision_digest_empty_input_is_report_only_noop() -> None:
    summary = report(())

    assert summary.digest_status == "ready"
    assert summary.recommended_next_step == (
        "allow_report_only_market_research_nonfarm_payroll_revision_digest"
    )
    assert summary.reason_codes == (
        "market_research_nonfarm_payroll_revision_digest_no_inputs",
    )
    assert summary.release_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == ()
    assert summary.average_revision_abs_jobs == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_nonfarm_payroll_revision_digest_payload_is_stable_json_ready_and_decimal_only() -> None:
    ready_summary = report((input_row(),))
    watched_summary = report(
        (
            input_row(
                source_count=d("1.000000"),
                previous_payroll_jobs=d("150000"),
                revised_payroll_jobs=d("225000"),
            ),
        ),
    )
    payload = market_research_nonfarm_payroll_revision_digest_payload(ready_summary)

    assert json.loads(json.dumps(payload))["digest_status"] == "ready"
    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["release_count"] == "1.000000"
    assert payload["rows"][0]["released_at"] == "2026-07-03T15:15:00+00:00"
    assert payload["rows"][0]["acknowledgement_lag_seconds"] == "900.000000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["revision_abs_jobs"] == "35000.000000"
    assert payload["reason_code_counts"] == []

    decimal_field_names = {
        "release_count",
        "ready_release_count",
        "watch_release_count",
        "blocked_release_count",
        "material_revision_count",
        "stale_release_count",
        "thin_source_count",
        "missing_acknowledgement_count",
        "slow_acknowledgement_count",
        "probability_repricing_count",
        "average_revision_abs_jobs",
        "max_release_age_seconds",
        "average_source_count",
    }
    for field_name in decimal_field_names:
        value = getattr(ready_summary, field_name)
        assert type(value) is Decimal
        assert value.as_tuple().exponent == -6

    row = ready_summary.rows[0]
    for field_name in (
        "release_age_seconds",
        "acknowledgement_lag_seconds",
        "source_count",
        "previous_payroll_jobs",
        "revised_payroll_jobs",
        "consensus_payroll_jobs",
        "revision_delta_jobs",
        "revision_abs_jobs",
        "consensus_delta_jobs",
        "unemployment_rate",
        "labor_force_participation_rate",
        "market_probability_before",
        "market_probability_after",
        "probability_delta",
    ):
        value = getattr(row, field_name)
        assert type(value) is Decimal
        assert value.as_tuple().exponent == -6

    count_row = watched_summary.reason_code_counts[0]
    assert type(count_row.count) is Decimal
    assert type(count_row.release_ratio) is Decimal
    assert count_row.count.as_tuple().exponent == -6
    assert count_row.release_ratio.as_tuple().exponent == -6

    with pytest.raises(ValueError, match="public float or int"):
        market_research_nonfarm_payroll_revision_digest_payload(1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="public float or int"):
        market_research_nonfarm_payroll_revision_digest_payload(0.1)  # type: ignore[arg-type]


def test_nonfarm_payroll_revision_digest_dataclasses_are_frozen_and_exact_types() -> None:
    summary = report((input_row(),))

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].revision_status = "watch"  # type: ignore[misc]

    assert type(summary) is MarketResearchNonfarmPayrollRevisionDigestReport
    assert type(summary.rows[0]) is MarketResearchNonfarmPayrollRevisionDigestRow
    assert is_dataclass(MarketResearchNonfarmPayrollRevisionDigestConfig())
    assert is_dataclass(MarketResearchNonfarmPayrollRevisionDigestInputRow)
    assert is_dataclass(MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount)

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(MarketResearchNonfarmPayrollRevisionDigestConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class InputSubclass(MarketResearchNonfarmPayrollRevisionDigestInputRow):
            pass


def test_nonfarm_payroll_revision_digest_validates_utc_flags_inputs_and_temporal_order() -> None:
    aware_plus_two = datetime(2026, 7, 3, 17, 0, tzinfo=timezone(timedelta(hours=1)))
    row = input_row(released_at=aware_plus_two, acknowledged_at=aware_plus_two)

    assert row.released_at == datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
    assert row.released_at.tzinfo is UTC
    assert row.acknowledged_at == datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
    assert row.acknowledged_at.tzinfo is UTC

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report((input_row(),), generated_at=datetime(2026, 7, 3, 16, 0))

    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report((input_row(),), generated_at=_DateTimeSubclass(2026, 7, 3, 16, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            (input_row(),),
            generated_at=datetime(2026, 7, 3, 16, 0, tzinfo=NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="released_at must be timezone-aware"):
        input_row(released_at=datetime(2026, 7, 3, 15, 0))

    with pytest.raises(ValueError, match="acknowledged_at must not precede released_at"):
        input_row(
            released_at=GENERATED_AT - timedelta(minutes=10),
            acknowledged_at=GENERATED_AT - timedelta(minutes=20),
        )

    with pytest.raises(ValueError, match="released_at must not be after generated_at"):
        report(
            (
                input_row(
                    released_at=GENERATED_AT + timedelta(seconds=1),
                    acknowledged_at=GENERATED_AT + timedelta(seconds=2),
                ),
            ),
        )

    with pytest.raises(ValueError, match="paper_only/report_only/readonly must be True"):
        input_row(paper_only=False)

    with pytest.raises(ValueError, match="config must be exactly"):
        report((input_row(),), cfg=object())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="input row must be exactly"):
        report((object(),))


def test_nonfarm_payroll_revision_digest_rejects_non_decimal_public_numbers_and_sensitive_surface() -> None:
    with pytest.raises(ValueError, match="source_count must be exactly Decimal"):
        input_row(source_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="previous_payroll_jobs must be exactly Decimal"):
        input_row(previous_payroll_jobs=_DecimalSubclass("150000"))

    with pytest.raises(ValueError, match="source_count must be a whole-count Decimal"):
        input_row(source_count=d("1.500000"))

    with pytest.raises(ValueError, match="unemployment_rate must be between"):
        input_row(unemployment_rate=d("1.000001"))

    with pytest.raises(ValueError, match="release_reference contains forbidden text"):
        input_row(release_reference="wallet-private-source")

    with pytest.raises(ValueError, match="research_key must be a plain string"):
        input_row(research_key=_StringSubclass("research.nfp.subclass"))


def test_nonfarm_payroll_revision_digest_source_contains_no_durable_or_trading_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_nonfarm_payroll_revision_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
        "eth_account",
    }
    forbidden_calls = {"open", "connect", "request", "urlopen", "Session"}
    forbidden_text = (
        "wallet",
        "broker",
        "order",
        "trade",
        "auth",
        "token",
        "secret",
        "database",
        "persist",
    )

    assert forbidden_imports.isdisjoint(imported_modules)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_calls
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_calls
    lower_source = source.lower()
    assert all(fragment not in lower_source for fragment in forbidden_text)


def test_nonfarm_payroll_revision_digest_manual_report_construction_normalizes_and_validates() -> None:
    row = MarketResearchNonfarmPayrollRevisionDigestRow(
        research_key="research.nfp.manual",
        condition_id="condition_manual",
        payroll_series_key="manual.nonfarm_payrolls",
        revision_status="ready",
        released_at=datetime(2026, 7, 3, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
        acknowledged_at=datetime(2026, 7, 3, 12, 15, tzinfo=timezone(timedelta(hours=-4))),
        release_age_seconds=d("0"),
        acknowledgement_lag_seconds=d("900"),
        source_count=d("1"),
        previous_payroll_jobs=d("150000"),
        revised_payroll_jobs=d("160000"),
        consensus_payroll_jobs=d("155000"),
        revision_delta_jobs=d("10000"),
        revision_abs_jobs=d("10000"),
        consensus_delta_jobs=d("5000"),
        unemployment_rate=d("0.041"),
        labor_force_participation_rate=d("0.626"),
        market_probability_before=d("0.400000"),
        market_probability_after=d("0.450000"),
        probability_delta=d("0.050000"),
        redacted_release_reference="public-manual",
        reason_codes=("market_research_nonfarm_payroll_revision_digest_ready",),
    )
    count = MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount(
        reason_code="market_research_nonfarm_payroll_revision_digest_ready",
        count=d("1"),
        release_ratio=d("1"),
    )
    summary = MarketResearchNonfarmPayrollRevisionDigestReport(
        generated_at=datetime(2026, 7, 3, 12, 30, tzinfo=timezone(timedelta(hours=-4))),
        config_version=(
            DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLL_REVISION_DIGEST_CONFIG_VERSION
        ),
        digest_status="ready",
        recommended_next_step=(
            "allow_report_only_market_research_nonfarm_payroll_revision_digest"
        ),
        reason_codes=("market_research_nonfarm_payroll_revision_digest_ready",),
        release_count=d("1"),
        ready_release_count=d("1"),
        watch_release_count=d("0"),
        blocked_release_count=d("0"),
        material_revision_count=d("0"),
        stale_release_count=d("0"),
        thin_source_count=d("0"),
        missing_acknowledgement_count=d("0"),
        slow_acknowledgement_count=d("0"),
        probability_repricing_count=d("0"),
        average_revision_abs_jobs=d("10000"),
        max_release_age_seconds=d("1800"),
        average_source_count=d("1"),
        rows=(row,),
        reason_code_counts=(count,),
    )

    assert summary.generated_at == datetime(2026, 7, 3, 16, 30, tzinfo=UTC)
    assert summary.generated_at.tzinfo is UTC
    assert summary.rows[0].released_at == datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
    assert summary.rows[0].acknowledgement_lag_seconds == d("900.000000")
    assert summary.reason_code_counts[0].release_ratio == d("1.000000")

    with pytest.raises(ValueError, match="ready count fields must sum"):
        replace(summary, ready_release_count=d("0"))

    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(
            summary,
            reason_codes=(
                "market_research_nonfarm_payroll_revision_digest_thin_sources",
                "market_research_nonfarm_payroll_revision_digest_material_revision",
            ),
        )
