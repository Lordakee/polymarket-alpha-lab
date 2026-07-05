from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_economic_calendar_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_ECONOMIC_CALENDAR_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchEconomicCalendarSurpriseDigestConfig,
    MarketResearchEconomicCalendarSurpriseDigestInputRow,
    MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount,
    MarketResearchEconomicCalendarSurpriseDigestReport,
    MarketResearchEconomicCalendarSurpriseDigestRow,
    build_market_research_economic_calendar_surprise_digest,
    market_research_economic_calendar_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchEconomicCalendarSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_ECONOMIC_CALENDAR_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("3600.000000"),
        "min_source_count": d("2"),
        "material_surprise_threshold": d("0.050000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchEconomicCalendarSurpriseDigestConfig(**values)


def input_row(
    research_key: str = "research.calendar.cpi",
    *,
    condition_id: str = "condition_cpi",
    calendar_event_key: str = "calendar.cpi",
    calendar_event_family: str = "inflation",
    calendar_event_reference: str = "public-cpi-calendar",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("2"),
    forecast_value: Decimal = d("3.200000"),
    actual_value: Decimal = d("3.250000"),
    surprise_score: Decimal = d("0.020000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEconomicCalendarSurpriseDigestInputRow:
    return MarketResearchEconomicCalendarSurpriseDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        calendar_event_key=calendar_event_key,
        calendar_event_family=calendar_event_family,
        calendar_event_reference=calendar_event_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=10)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        forecast_value=forecast_value,
        actual_value=actual_value,
        surprise_score=surprise_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchEconomicCalendarSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEconomicCalendarSurpriseDigestReport:
    return build_market_research_economic_calendar_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_calendar_surprise_digest_reduces_rows_redacts_refs_and_sorts_deterministically() -> None:
    summary = report(
        (
            input_row(
                "research.calendar.payrolls",
                condition_id="condition_payrolls",
                calendar_event_key="calendar.payrolls",
                calendar_event_family="labor",
                calendar_event_reference="https://vendor.example/jobs?token=secret-123",
                released_at=GENERATED_AT - timedelta(hours=2),
                acknowledged_at=GENERATED_AT - timedelta(minutes=80),
                source_count=d("1"),
                forecast_value=d("150000.000000"),
                actual_value=d("245000.000000"),
                surprise_score=d("0.080000"),
            ),
            input_row(
                "research.calendar.cpi",
                condition_id="condition_cpi",
                calendar_event_key="calendar.cpi",
                calendar_event_family="inflation",
                calendar_event_reference="public-cpi-calendar",
                released_at=GENERATED_AT - timedelta(minutes=40),
                acknowledged_at=GENERATED_AT - timedelta(minutes=35),
                source_count=d("3"),
                forecast_value=d("3.200000"),
                actual_value=d("3.250000"),
                surprise_score=d("0.020000"),
            ),
            input_row(
                "research.calendar.ism",
                condition_id="condition_ism",
                calendar_event_key="calendar.ism",
                calendar_event_family="growth",
                calendar_event_reference="private-macro-feed",
                released_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=None,
                source_count=d("2"),
                forecast_value=d("49.000000"),
                actual_value=d("44.000000"),
                surprise_score=d("0.060000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_ECONOMIC_CALENDAR_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_economic_calendar_surprise_digest"
    )
    assert summary.calendar_event_count == d("3")
    assert summary.ready_event_count == d("1")
    assert summary.watch_event_count == d("1")
    assert summary.blocked_event_count == d("1")
    assert summary.material_surprise_count == d("2")
    assert summary.stale_release_count == d("2")
    assert summary.thin_source_count == d("1")
    assert summary.missing_acknowledgement_count == d("1")
    assert summary.slow_acknowledgement_count == d("1")
    assert summary.average_surprise_score == d("0.053333")
    assert summary.max_release_age_seconds == d("14400.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.calendar_event_key for row in summary.rows) == (
        "calendar.ism",
        "calendar.payrolls",
        "calendar.cpi",
    )

    ism = summary.rows[0]
    assert ism.surprise_status == "blocked"
    assert ism.release_age_seconds == d("14400.000000")
    assert ism.acknowledgement_lag_seconds is None
    assert ism.surprise_delta == d("-5.000000")
    assert ism.redacted_calendar_event_reference == "sha256:5f9a898d0e3f"
    assert ism.reason_codes == (
        "market_research_economic_calendar_surprise_digest_material_surprise",
        "market_research_economic_calendar_surprise_digest_missing_acknowledgement",
        "market_research_economic_calendar_surprise_digest_stale_release",
    )

    payrolls = summary.rows[1]
    assert payrolls.surprise_status == "watch"
    assert payrolls.release_age_seconds == d("7200.000000")
    assert payrolls.acknowledgement_lag_seconds == d("2400.000000")
    assert payrolls.surprise_delta == d("95000.000000")
    assert payrolls.redacted_calendar_event_reference == "sha256:32f5117c9372"
    assert payrolls.reason_codes == (
        "market_research_economic_calendar_surprise_digest_material_surprise",
        "market_research_economic_calendar_surprise_digest_slow_acknowledgement",
        "market_research_economic_calendar_surprise_digest_stale_release",
        "market_research_economic_calendar_surprise_digest_thin_sources",
    )

    cpi = summary.rows[2]
    assert cpi.surprise_status == "ready"
    assert cpi.release_age_seconds == d("2400.000000")
    assert cpi.acknowledgement_lag_seconds == d("300.000000")
    assert cpi.surprise_delta == d("0.050000")
    assert cpi.redacted_calendar_event_reference == "public-cpi-calendar"
    assert cpi.reason_codes == (
        "market_research_economic_calendar_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount(
            reason_code="market_research_economic_calendar_surprise_digest_material_surprise",
            count=d("2"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount(
            reason_code="market_research_economic_calendar_surprise_digest_stale_release",
            count=d("2"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_economic_calendar_surprise_digest_"
                "missing_acknowledgement"
            ),
            count=d("1"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount(
            reason_code="market_research_economic_calendar_surprise_digest_ready",
            count=d("1"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_economic_calendar_surprise_digest_"
                "slow_acknowledgement"
            ),
            count=d("1"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount(
            reason_code="market_research_economic_calendar_surprise_digest_thin_sources",
            count=d("1"),
            event_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "private-macro-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_empty_calendar_surprise_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_economic_calendar_surprise_digest"
    )
    assert summary.calendar_event_count == ZERO
    assert summary.ready_event_count == ZERO
    assert summary.watch_event_count == ZERO
    assert summary.blocked_event_count == ZERO
    assert summary.average_surprise_score == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount(
            reason_code="market_research_economic_calendar_surprise_digest_no_inputs",
            count=d("1.000000"),
            event_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_economic_calendar_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_calendar_surprise_digest_payload_uses_decimal_strings_and_omits_sensitive_refs() -> None:
    summary = report((input_row(),))
    payload = market_research_economic_calendar_surprise_digest_payload(summary)

    assert payload["calendar_event_count"] == "1.000000"
    assert payload["average_surprise_score"] == "0.020000"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'calendar_event_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_calendar_surprise_digest_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchEconomicCalendarSurpriseDigestConfig)
    assert is_dataclass(MarketResearchEconomicCalendarSurpriseDigestInputRow)
    assert is_dataclass(MarketResearchEconomicCalendarSurpriseDigestRow)
    assert is_dataclass(MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount)
    assert is_dataclass(MarketResearchEconomicCalendarSurpriseDigestReport)

    with pytest.raises(TypeError, match="subclassing"):

        class ConfigSubclass(MarketResearchEconomicCalendarSurpriseDigestConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class InputRowSubclass(MarketResearchEconomicCalendarSurpriseDigestInputRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class RowSubclass(MarketResearchEconomicCalendarSurpriseDigestRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class ReasonCodeCountSubclass(
            MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class ReportSubclass(MarketResearchEconomicCalendarSurpriseDigestReport):
            pass

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("3")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("calendar-surprise-v0"))
    with pytest.raises(ValueError, match="fresh_release_max_age_seconds"):
        config(fresh_release_max_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.5"))
    with pytest.raises(ValueError, match="material_surprise_threshold"):
        config(material_surprise_threshold=Decimal("NaN"))
    with pytest.raises(ValueError, match="max_acknowledgement_lag_seconds"):
        config(max_acknowledgement_lag_seconds=_DecimalSubclass("1800"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="calendar_event_family"):
        input_row(calendar_event_family="broker_feed")
    with pytest.raises(ValueError, match="released_at"):
        input_row(released_at=datetime(2026, 7, 3, 14, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(released_at=datetime(2026, 7, 3, 14, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(acknowledged_at=_DatetimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(acknowledged_at=datetime(2026, 7, 3, 14, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_value"):
        input_row(forecast_value=Decimal("Infinity"))
    with pytest.raises(ValueError, match="actual_value"):
        input_row(actual_value=_DecimalSubclass("3.250000"))
    with pytest.raises(ValueError, match="surprise_score"):
        input_row(surprise_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_economic_calendar_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_economic_calendar_surprise_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        build_market_research_economic_calendar_surprise_digest(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 3, 14, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_hard_report_only_flags_reject_false_values_for_all_public_records() -> None:
    summary = report((input_row(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]
    public_record_factories = (
        ("config", lambda **kwargs: config(**kwargs)),
        ("input row", lambda **kwargs: input_row(**kwargs)),
        ("row", lambda **kwargs: replace(row, **kwargs)),
        ("reason count", lambda **kwargs: replace(reason_count, **kwargs)),
        ("report", lambda **kwargs: replace(summary, **kwargs)),
    )

    for label, factory in public_record_factories:
        for flag_name in ("paper_only", "report_only", "readonly"):
            with pytest.raises(
                ValueError,
                match=f"{label} {flag_name} must be True",
            ):
                factory(**{flag_name: False})


def test_report_and_row_consistency_rejects_incoherent_manual_constructors() -> None:
    ready = report((input_row(),)).rows[0]
    finding_summary = report(
        (
            input_row(
                "research.calendar.payrolls",
                calendar_event_key="calendar.payrolls",
                surprise_score=d("0.080000"),
            ),
            input_row(),
        ),
    )

    with pytest.raises(ValueError, match="count"):
        MarketResearchEconomicCalendarSurpriseDigestReasonCodeCount(
            reason_code="market_research_economic_calendar_surprise_digest_no_inputs",
            count=ZERO,
            event_ratio=ZERO,
        )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_economic_calendar_surprise_digest_ready",
                "market_research_economic_calendar_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="surprise_status"):
        replace(ready, surprise_status="blocked")
    with pytest.raises(ValueError, match="surprise_delta"):
        replace(ready, surprise_delta=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_calendar_event_reference"):
        replace(ready, redacted_calendar_event_reference="https://host?token=secret")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            finding_summary,
            reason_code_counts=tuple(reversed(finding_summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(finding_summary, reason_codes=tuple(reversed(finding_summary.reason_codes)))

    with pytest.raises(ValueError, match="ready_event_count"):
        replace(report((input_row(),)), ready_event_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        two_row_report = report(
            (
                input_row("research.calendar.z", calendar_event_key="calendar.z"),
                input_row(),
            ),
        )
        replace(two_row_report, rows=tuple(reversed(two_row_report.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_economic_calendar_surprise_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    assert "persist" not in source.lower()
    assert "database" not in source.lower()
    assert "advice" not in source.lower()


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "count",
        "delta",
        "lag",
        "ratio",
        "score",
        "value",
    )
    for field in value.__dataclass_fields__.values():
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            if field_value is None:
                continue
            assert type(field_value) is Decimal, field.name
