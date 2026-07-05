from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import importlib
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_payroll_hours_worked_digest import (
    DEFAULT_MARKET_RESEARCH_PAYROLL_HOURS_WORKED_DIGEST_CONFIG_VERSION,
    MarketResearchPayrollHoursWorkedDigestConfig,
    MarketResearchPayrollHoursWorkedDigestInputRow,
    MarketResearchPayrollHoursWorkedDigestReasonCodeCount,
    build_market_research_payroll_hours_worked_digest,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchPayrollHoursWorkedDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_PAYROLL_HOURS_WORKED_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("7200.000000"),
        "material_hours_delta_threshold": d("0.100000"),
        "min_source_count": d("2.000000"),
        "probability_repricing_threshold": d("0.050000"),
    }
    values.update(overrides)
    return MarketResearchPayrollHoursWorkedDigestConfig(**values)


def input_row(
    research_key: str = "research.hours.production",
    *,
    condition_id: str = "condition_hours_worked",
    payroll_series_key: str = "ces.average_weekly_hours",
    released_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    actual_hours_worked: Decimal = d("34.450000"),
    consensus_hours_worked: Decimal = d("34.400000"),
    previous_hours_worked: Decimal = d("34.425000"),
    market_probability_before: Decimal = d("0.500000"),
    market_probability_after: Decimal = d("0.520000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPayrollHoursWorkedDigestInputRow:
    return MarketResearchPayrollHoursWorkedDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        payroll_series_key=payroll_series_key,
        released_at=released_at or GENERATED_AT - timedelta(minutes=45),
        source_count=source_count,
        actual_hours_worked=actual_hours_worked,
        consensus_hours_worked=consensus_hours_worked,
        previous_hours_worked=previous_hours_worked,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_payroll_hours_worked_digest_reduces_rows_sorts_and_reasons_deterministically() -> None:
    report = build_market_research_payroll_hours_worked_digest(
        (
            input_row(
                "research.hours.services",
                condition_id="condition_services_hours",
                payroll_series_key="ces.service_hours",
                released_at=GENERATED_AT - timedelta(hours=4),
                source_count=d("1.000000"),
                actual_hours_worked=d("33.900000"),
                consensus_hours_worked=d("34.100000"),
                previous_hours_worked=d("34.000000"),
                market_probability_before=d("0.410000"),
                market_probability_after=d("0.440000"),
            ),
            input_row(
                "research.hours.mfg",
                condition_id="condition_mfg_hours",
                payroll_series_key="ces.manufacturing_hours",
                released_at=GENERATED_AT - timedelta(hours=3),
                source_count=d("2.000000"),
                actual_hours_worked=d("40.600000"),
                consensus_hours_worked=d("40.450000"),
                previous_hours_worked=d("40.500000"),
                market_probability_before=d("0.460000"),
                market_probability_after=d("0.570000"),
            ),
            input_row(),
        ),
        config=config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_MARKET_RESEARCH_PAYROLL_HOURS_WORKED_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_market_research_payroll_hours_worked_digest"
    )
    assert report.release_count == d("3.000000")
    assert report.ready_release_count == d("1.000000")
    assert report.watch_release_count == d("2.000000")
    assert report.blocked_release_count == ZERO
    assert report.positive_hours_surprise_count == d("2.000000")
    assert report.negative_hours_surprise_count == d("1.000000")
    assert report.material_hours_surprise_count == d("2.000000")
    assert report.stale_release_count == d("2.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.probability_repricing_count == d("1.000000")
    assert report.positive_hours_surprise_ratio == d("0.666667")
    assert report.negative_hours_surprise_ratio == d("0.333333")
    assert report.material_hours_surprise_ratio == d("0.666667")
    assert report.average_abs_hours_surprise == d("0.133333")
    assert report.max_release_age_seconds == d("14400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.digest_status, row.payroll_series_key) for row in report.rows) == (
        ("watch", "ces.manufacturing_hours"),
        ("watch", "ces.service_hours"),
        ("ready", "ces.average_weekly_hours"),
    )

    mfg = report.rows[0]
    assert mfg.released_at == datetime(2026, 7, 3, 13, 0, tzinfo=UTC)
    assert mfg.release_age_seconds == d("10800.000000")
    assert mfg.hours_surprise == d("0.150000")
    assert mfg.hours_surprise_abs == d("0.150000")
    assert mfg.hours_surprise_ratio == d("0.003708")
    assert mfg.previous_hours_delta == d("0.100000")
    assert mfg.probability_delta == d("0.110000")
    assert mfg.reason_codes == (
        "market_research_payroll_hours_worked_digest_material_hours_surprise",
        "market_research_payroll_hours_worked_digest_positive_hours_surprise",
        "market_research_payroll_hours_worked_digest_probability_repricing",
        "market_research_payroll_hours_worked_digest_stale_release",
    )

    services = report.rows[1]
    assert services.hours_surprise == d("-0.200000")
    assert services.hours_surprise_abs == d("0.200000")
    assert services.reason_codes == (
        "market_research_payroll_hours_worked_digest_material_hours_surprise",
        "market_research_payroll_hours_worked_digest_negative_hours_surprise",
        "market_research_payroll_hours_worked_digest_stale_release",
        "market_research_payroll_hours_worked_digest_thin_sources",
    )

    ready = report.rows[2]
    assert ready.digest_status == "ready"
    assert ready.reason_codes == (
        "market_research_payroll_hours_worked_digest_ready",
    )

    assert report.reason_codes == (
        "market_research_payroll_hours_worked_digest_material_hours_surprise",
        "market_research_payroll_hours_worked_digest_negative_hours_surprise",
        "market_research_payroll_hours_worked_digest_positive_hours_surprise",
        "market_research_payroll_hours_worked_digest_probability_repricing",
        "market_research_payroll_hours_worked_digest_stale_release",
        "market_research_payroll_hours_worked_digest_thin_sources",
    )
    assert report.reason_code_counts == (
        MarketResearchPayrollHoursWorkedDigestReasonCodeCount(
            reason_code=(
                "market_research_payroll_hours_worked_digest_material_hours_surprise"
            ),
            count=d("2.000000"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchPayrollHoursWorkedDigestReasonCodeCount(
            reason_code="market_research_payroll_hours_worked_digest_stale_release",
            count=d("2.000000"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchPayrollHoursWorkedDigestReasonCodeCount(
            reason_code=(
                "market_research_payroll_hours_worked_digest_probability_repricing"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchPayrollHoursWorkedDigestReasonCodeCount(
            reason_code=(
                "market_research_payroll_hours_worked_digest_negative_hours_surprise"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchPayrollHoursWorkedDigestReasonCodeCount(
            reason_code=(
                "market_research_payroll_hours_worked_digest_positive_hours_surprise"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchPayrollHoursWorkedDigestReasonCodeCount(
            reason_code="market_research_payroll_hours_worked_digest_thin_sources",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
    )


def test_payroll_hours_worked_digest_empty_input_is_blocked_report_only() -> None:
    report = build_market_research_payroll_hours_worked_digest(
        (),
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_payroll_hours_worked_digest"
    )
    assert report.reason_codes == (
        "market_research_payroll_hours_worked_digest_no_inputs",
    )
    assert report.release_count == ZERO
    assert report.rows == ()
    assert report.reason_code_counts == (
        MarketResearchPayrollHoursWorkedDigestReasonCodeCount(
            reason_code="market_research_payroll_hours_worked_digest_no_inputs",
            count=d("1.000000"),
            release_ratio=ZERO,
        ),
    )
    assert report.average_abs_hours_surprise == ZERO
    assert report.max_release_age_seconds == ZERO
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payroll_hours_worked_dataclasses_are_frozen_and_decimal_only() -> None:
    row = input_row()

    with pytest.raises(FrozenInstanceError):
        row.research_key = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="actual_hours_worked must be a Decimal"):
        input_row(actual_hours_worked=34.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="actual_hours_worked must be a Decimal"):
        input_row(actual_hours_worked=_DecimalSubclass("34.500000"))

    with pytest.raises(ValueError, match="source_count must be an integral Decimal"):
        input_row(source_count=d("1.500000"))

    with pytest.raises(ValueError, match="market_probability_after must be between 0 and 1"):
        input_row(market_probability_after=d("1.010000"))

    report = build_market_research_payroll_hours_worked_digest(
        (row,),
        config=config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].digest_status = "blocked"  # type: ignore[misc]

    public_report_decimal_fields = (
        "release_count",
        "ready_release_count",
        "watch_release_count",
        "blocked_release_count",
        "positive_hours_surprise_count",
        "negative_hours_surprise_count",
        "material_hours_surprise_count",
        "stale_release_count",
        "thin_source_count",
        "probability_repricing_count",
        "positive_hours_surprise_ratio",
        "negative_hours_surprise_ratio",
        "material_hours_surprise_ratio",
        "average_abs_hours_surprise",
        "max_release_age_seconds",
    )
    assert all(type(getattr(report, name)) is Decimal for name in public_report_decimal_fields)
    assert all(
        type(getattr(report.rows[0], name)) is Decimal
        for name in (
            "release_age_seconds",
            "source_count",
            "actual_hours_worked",
            "consensus_hours_worked",
            "previous_hours_worked",
            "market_probability_before",
            "market_probability_after",
            "hours_surprise",
            "hours_surprise_abs",
            "hours_surprise_ratio",
            "previous_hours_delta",
            "probability_delta",
        )
    )
    for public_record in (
        config(),
        row,
        report.rows[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name


def test_payroll_hours_worked_digest_rejects_unsafe_scope_and_bad_inputs() -> None:
    with pytest.raises(ValueError, match="released_at must be timezone-aware"):
        input_row(released_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="released_at must be timezone-aware"):
        input_row(released_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTZ()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_market_research_payroll_hours_worked_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_market_research_payroll_hours_worked_digest(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTZ()),
        )

    with pytest.raises(ValueError, match="released_at must not be in the future"):
        build_market_research_payroll_hours_worked_digest(
            (input_row(released_at=GENERATED_AT + timedelta(seconds=1)),),
            config=config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="input row paper_only must be True"):
        input_row(paper_only=False)

    with pytest.raises(ValueError, match="config readonly must be True"):
        config(readonly=False)

    with pytest.raises(
        ValueError,
        match="config must be a MarketResearchPayrollHoursWorkedDigestConfig",
    ):
        build_market_research_payroll_hours_worked_digest(
            (input_row(),),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="inputs must be a list or tuple"):
        build_market_research_payroll_hours_worked_digest(
            "bad",  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(
        ValueError,
        match="inputs must contain MarketResearchPayrollHoursWorkedDigestInputRow values",
    ):
        build_market_research_payroll_hours_worked_digest(
            (object(),),  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_payroll_hours_worked_digest_rejects_false_flags_on_public_records() -> None:
    report = build_market_research_payroll_hours_worked_digest(
        (input_row(actual_hours_worked=d("34.700000")),),
        config=config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason count report_only must be True"):
        replace(report.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(report, paper_only=False)


def test_payroll_hours_worked_digest_is_input_order_invariant() -> None:
    blocked = input_row(
        "research.hours.blocked",
        condition_id="condition_blocked_hours",
        payroll_series_key="ces.blocked_hours",
        source_count=d("1.000000"),
        actual_hours_worked=d("34.420000"),
        consensus_hours_worked=d("34.400000"),
    )
    watch = input_row(
        "research.hours.watch",
        condition_id="condition_watch_hours",
        payroll_series_key="ces.watch_hours",
        actual_hours_worked=d("34.650000"),
        consensus_hours_worked=d("34.400000"),
    )
    ready = input_row(
        "research.hours.ready",
        condition_id="condition_ready_hours",
        payroll_series_key="ces.ready_hours",
    )

    forward = build_market_research_payroll_hours_worked_digest(
        (ready, watch, blocked),
        config=config(),
        generated_at=GENERATED_AT,
    )
    reverse = build_market_research_payroll_hours_worked_digest(
        (blocked, watch, ready),
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert forward == reverse
    assert tuple(row.payroll_series_key for row in forward.rows) == (
        "ces.blocked_hours",
        "ces.watch_hours",
        "ces.ready_hours",
    )

    with pytest.raises(ValueError, match="reason_codes must use deterministic ordering"):
        replace(forward.rows[1], reason_codes=tuple(reversed(forward.rows[1].reason_codes)))
    with pytest.raises(ValueError, match="rows must use deterministic ordering"):
        replace(forward, rows=tuple(reversed(forward.rows)))


def test_payroll_hours_worked_digest_payload_serializes_strings_and_safe_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_payroll_hours_worked_digest",
    )
    report = build_market_research_payroll_hours_worked_digest(
        (input_row(actual_hours_worked=d("34.700000")),),
        config=config(),
        generated_at=GENERATED_AT,
    )

    payload = module.market_research_payroll_hours_worked_digest_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["release_count"] == "1.000000"
    assert payload["average_abs_hours_surprise"] == "0.300000"
    assert payload["rows"][0]["released_at"] == "2026-07-03T15:15:00+00:00"
    assert payload["rows"][0]["actual_hours_worked"] == "34.700000"
    assert payload["rows"][0]["hours_surprise"] == "0.300000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"

    with pytest.raises(
        ValueError,
        match="report must be exactly MarketResearchPayrollHoursWorkedDigestReport",
    ):
        module.market_research_payroll_hours_worked_digest_payload(object())

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "auth" not in lowered
                assert "api_key" not in lowered
                assert "private" not in lowered
                assert "secret" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)


def test_payroll_hours_worked_digest_public_surface_is_pure_report_only() -> None:
    import polymarket_alpha_lab.market_research_payroll_hours_worked_digest as digest

    forbidden_names = (
        "account",
        "auth",
        "cancel",
        "db",
        "network",
        "open",
        "order",
        "private_key",
        "replace",
        "requests",
        "session",
        "socket",
        "sqlite",
        "supabase",
        "trade",
        "wallet",
    )

    assert all(not hasattr(digest, name) for name in forbidden_names)
    assert digest.__all__ == (
        "DEFAULT_MARKET_RESEARCH_PAYROLL_HOURS_WORKED_DIGEST_CONFIG_VERSION",
        "MarketResearchPayrollHoursWorkedDigestConfig",
        "MarketResearchPayrollHoursWorkedDigestInputRow",
        "MarketResearchPayrollHoursWorkedDigestRow",
        "MarketResearchPayrollHoursWorkedDigestReasonCodeCount",
        "MarketResearchPayrollHoursWorkedDigestReport",
        "build_market_research_payroll_hours_worked_digest",
        "market_research_payroll_hours_worked_digest_payload",
    )

    source = Path(
        "src/polymarket_alpha_lab/market_research_payroll_hours_worked_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "supabase",
        "urllib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "api_key",
        "cancel_order",
        "connect(",
        "execute(",
        "exchange mutation",
        "live trading",
        "private_key",
        "read_text(",
        "replace_order",
        "secret",
        "submit_order",
        "urlopen",
        "wallet",
        "write_text(",
    ):
        assert forbidden not in source.lower()
