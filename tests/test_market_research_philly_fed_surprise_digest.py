from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_philly_fed_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_PHILLY_FED_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchPhillyFedSurpriseDigestConfig,
    MarketResearchPhillyFedSurpriseDigestInputRow,
    MarketResearchPhillyFedSurpriseDigestReasonCodeCount,
    MarketResearchPhillyFedSurpriseDigestReport,
    MarketResearchPhillyFedSurpriseDigestRow,
    build_market_research_philly_fed_surprise_digest,
    market_research_philly_fed_surprise_digest_payload,
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
    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchPhillyFedSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_PHILLY_FED_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("3600.000000"),
        "min_source_count": d("2"),
        "material_surprise_threshold_points": d("5.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchPhillyFedSurpriseDigestConfig(**values)


def input_row(
    research_key: str = "research.philly_fed.headline",
    *,
    condition_id: str = "condition_philly_fed",
    release_key: str = "philly_fed.2026_07",
    release_reference: str = "public-philly-fed-calendar",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("2"),
    forecast_index: Decimal = d("-2.000000"),
    actual_index: Decimal = d("1.500000"),
    prior_index: Decimal = d("-4.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPhillyFedSurpriseDigestInputRow:
    return MarketResearchPhillyFedSurpriseDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        release_key=release_key,
        release_reference=release_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=10)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        forecast_index=forecast_index,
        actual_index=actual_index,
        prior_index=prior_index,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchPhillyFedSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPhillyFedSurpriseDigestReport:
    return build_market_research_philly_fed_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_philly_fed_surprise_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.philly_fed.old_missing_ack",
                condition_id="condition_old_missing",
                release_key="philly_fed.2026_06",
                release_reference="https://vendor.example/philly?token=secret-123",
                released_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=None,
                source_count=d("2"),
                forecast_index=d("-8.000000"),
                actual_index=d("0.500000"),
                prior_index=d("-12.000000"),
            ),
            input_row(
                "research.philly_fed.ready",
                condition_id="condition_ready",
                release_key="philly_fed.2026_07",
                release_reference="public-philly-fed-calendar",
                released_at=GENERATED_AT - timedelta(minutes=30),
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                source_count=d("3"),
                forecast_index=d("-2.000000"),
                actual_index=d("1.500000"),
                prior_index=d("-4.000000"),
            ),
            input_row(
                "research.philly_fed.thin_slow",
                condition_id="condition_thin_slow",
                release_key="philly_fed.2026_08",
                release_reference="private-manufacturing-feed",
                released_at=GENERATED_AT - timedelta(hours=2),
                acknowledged_at=GENERATED_AT - timedelta(minutes=80),
                source_count=d("1"),
                forecast_index=d("4.000000"),
                actual_index=d("-3.000000"),
                prior_index=d("6.000000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_PHILLY_FED_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_philly_fed_surprise_digest"
    )
    assert summary.release_count == d("3.000000")
    assert summary.ready_release_count == d("1.000000")
    assert summary.watch_release_count == d("1.000000")
    assert summary.blocked_release_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_release_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.average_abs_surprise_points == d("6.333333")
    assert summary.max_release_age_seconds == d("14400.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.release_key for row in summary.rows) == (
        "philly_fed.2026_06",
        "philly_fed.2026_08",
        "philly_fed.2026_07",
    )

    old_missing = summary.rows[0]
    assert old_missing.surprise_status == "blocked"
    assert old_missing.release_age_seconds == d("14400.000000")
    assert old_missing.acknowledgement_lag_seconds is None
    assert old_missing.surprise_delta == d("8.500000")
    assert old_missing.abs_surprise_points == d("8.500000")
    assert old_missing.prior_delta == d("12.500000")
    assert old_missing.redacted_release_reference.startswith("sha256:")
    assert old_missing.reason_codes == (
        "market_research_philly_fed_surprise_digest_material_surprise",
        "market_research_philly_fed_surprise_digest_missing_acknowledgement",
        "market_research_philly_fed_surprise_digest_stale_release",
    )

    thin_slow = summary.rows[1]
    assert thin_slow.surprise_status == "watch"
    assert thin_slow.release_age_seconds == d("7200.000000")
    assert thin_slow.acknowledgement_lag_seconds == d("2400.000000")
    assert thin_slow.surprise_delta == d("-7.000000")
    assert thin_slow.abs_surprise_points == d("7.000000")
    assert thin_slow.prior_delta == d("-9.000000")
    assert thin_slow.redacted_release_reference.startswith("sha256:")
    assert thin_slow.reason_codes == (
        "market_research_philly_fed_surprise_digest_material_surprise",
        "market_research_philly_fed_surprise_digest_slow_acknowledgement",
        "market_research_philly_fed_surprise_digest_stale_release",
        "market_research_philly_fed_surprise_digest_thin_sources",
    )

    ready = summary.rows[2]
    assert ready.surprise_status == "ready"
    assert ready.release_age_seconds == d("1800.000000")
    assert ready.acknowledgement_lag_seconds == d("600.000000")
    assert ready.surprise_delta == d("3.500000")
    assert ready.abs_surprise_points == d("3.500000")
    assert ready.prior_delta == d("5.500000")
    assert ready.redacted_release_reference == "public-philly-fed-calendar"
    assert ready.reason_codes == (
        "market_research_philly_fed_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
            reason_code="market_research_philly_fed_surprise_digest_material_surprise",
            count=d("2.000000"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
            reason_code="market_research_philly_fed_surprise_digest_stale_release",
            count=d("2.000000"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_philly_fed_surprise_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
            reason_code="market_research_philly_fed_surprise_digest_ready",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_philly_fed_surprise_digest_"
                "slow_acknowledgement"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
            reason_code="market_research_philly_fed_surprise_digest_thin_sources",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
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
        "private-manufacturing-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "network",
        "database",
        "token",
        "secret",
        "private",
        "wallet",
        "order",
    ):
        assert token not in public


def test_empty_philly_fed_surprise_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_philly_fed_surprise_digest"
    )
    assert summary.release_count == ZERO
    assert summary.ready_release_count == ZERO
    assert summary.watch_release_count == ZERO
    assert summary.blocked_release_count == ZERO
    assert summary.average_abs_surprise_points == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
            reason_code="market_research_philly_fed_surprise_digest_no_inputs",
            count=d("1.000000"),
            release_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_philly_fed_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_philly_fed_sorting_breaks_ties_with_condition_id() -> None:
    row_b = input_row(
        "research.philly_fed.same_release",
        condition_id="condition_b",
        release_key="philly_fed.same_release",
    )
    row_a = input_row(
        "research.philly_fed.same_release",
        condition_id="condition_a",
        release_key="philly_fed.same_release",
    )

    expected_order = (
        ("condition_a", "philly_fed.same_release", "research.philly_fed.same_release"),
        ("condition_b", "philly_fed.same_release", "research.philly_fed.same_release"),
    )

    summary_from_ba = report((row_b, row_a))
    summary_from_ab = report((row_a, row_b))

    assert tuple(
        (row.condition_id, row.release_key, row.research_key)
        for row in summary_from_ba.rows
    ) == expected_order
    assert tuple(
        (row.condition_id, row.release_key, row.research_key)
        for row in summary_from_ab.rows
    ) == expected_order


def test_philly_fed_manual_public_records_reject_noncanonical_ordering() -> None:
    summary = report(
        (
            input_row(
                "research.philly_fed.old_missing_ack",
                condition_id="condition_old_missing",
                release_key="philly_fed.2026_06",
                released_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=None,
                forecast_index=d("-8.000000"),
                actual_index=d("0.500000"),
                prior_index=d("-12.000000"),
            ),
            input_row(
                "research.philly_fed.ready",
                condition_id="condition_ready",
                release_key="philly_fed.2026_07",
            ),
            input_row(
                "research.philly_fed.thin_slow",
                condition_id="condition_thin_slow",
                release_key="philly_fed.2026_08",
                released_at=GENERATED_AT - timedelta(hours=2),
                acknowledged_at=GENERATED_AT - timedelta(minutes=80),
                source_count=d("1.000000"),
                forecast_index=d("4.000000"),
                actual_index=d("-3.000000"),
                prior_index=d("6.000000"),
            ),
        ),
    )

    watch_row = summary.rows[1]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            watch_row,
            reason_codes=tuple(reversed(watch_row.reason_codes)),
        )

    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=tuple(reversed(summary.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=tuple(reversed(summary.reason_code_counts)))


def test_philly_fed_payload_uses_decimal_strings_and_omits_sensitive_refs() -> None:
    summary = report((input_row(release_reference="private-philly-feed"),))
    payload = market_research_philly_fed_surprise_digest_payload(summary)

    assert payload["release_count"] == "1.000000"
    assert payload["average_abs_surprise_points"] == "3.500000"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'release_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_philly_fed_payload_serializes_all_decimals_with_six_places() -> None:
    summary = report((input_row(),))
    payload = market_research_philly_fed_surprise_digest_payload(summary)

    for value in walk_values(payload):
        if isinstance(value, str) and value.replace(".", "", 1).isdigit():
            whole, dot, fractional = value.partition(".")
            assert whole
            assert dot == "."
            assert len(fractional) == 6


def test_philly_fed_rejects_tzinfo_with_missing_utc_offset() -> None:
    invalid_tz = _NoneOffsetTimezone()

    with pytest.raises(ValueError, match="UTC offset"):
        input_row(released_at=datetime(2026, 7, 3, 13, 40, tzinfo=invalid_tz))
    with pytest.raises(ValueError, match="UTC offset"):
        input_row(acknowledged_at=datetime(2026, 7, 3, 13, 50, tzinfo=invalid_tz))
    with pytest.raises(ValueError, match="UTC offset"):
        report((), generated_at=datetime(2026, 7, 3, 14, 0, tzinfo=invalid_tz))


def test_philly_fed_redacts_secret_key_replace_exchange_references() -> None:
    summary = report(
        (
            input_row(
                release_reference="exchange-replace-api-key-feed",
            ),
        ),
    )
    payload = market_research_philly_fed_surprise_digest_payload(summary)

    assert summary.rows[0].redacted_release_reference.startswith("sha256:")
    public = repr(payload).lower()
    assert "exchange-replace-api-key-feed" not in public
    assert "api-key" not in public
    assert "exchange" not in public
    assert "replace" not in public

    for kwargs in (
        {"research_key": "research.philly_fed.exchange"},
        {"condition_id": "condition_replace"},
        {"release_key": "philly_fed.api_key"},
    ):
        with pytest.raises(ValueError, match="public identifier"):
            input_row(**kwargs)


def test_philly_fed_surprise_digest_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchPhillyFedSurpriseDigestConfig)
    assert is_dataclass(MarketResearchPhillyFedSurpriseDigestInputRow)
    assert is_dataclass(MarketResearchPhillyFedSurpriseDigestRow)
    assert is_dataclass(MarketResearchPhillyFedSurpriseDigestReasonCodeCount)
    assert is_dataclass(MarketResearchPhillyFedSurpriseDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("3")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("philly-fed-v0"))
    with pytest.raises(ValueError, match="fresh_release_max_age_seconds"):
        config(fresh_release_max_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.5"))
    with pytest.raises(ValueError, match="material_surprise_threshold_points"):
        config(material_surprise_threshold_points=Decimal("NaN"))
    with pytest.raises(ValueError, match="max_acknowledgement_lag_seconds"):
        config(max_acknowledgement_lag_seconds=_DecimalSubclass("1800"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="release_key"):
        input_row(release_key="broker.feed")
    with pytest.raises(ValueError, match="released_at"):
        input_row(released_at=datetime(2026, 7, 3, 14, 0))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(acknowledged_at=_DatetimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_index"):
        input_row(forecast_index=Decimal("Infinity"))
    with pytest.raises(ValueError, match="actual_index"):
        input_row(actual_index=_DecimalSubclass("1.500000"))
    with pytest.raises(ValueError, match="prior_index"):
        input_row(prior_index=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_philly_fed_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_philly_fed_surprise_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_philly_fed_false_flags_are_rejected_on_every_public_surface() -> None:
    for kwargs in (
        {"paper_only": False},
        {"report_only": False},
        {"readonly": False},
    ):
        with pytest.raises(ValueError, match="paper_only/report_only/readonly"):
            config(**kwargs)
        with pytest.raises(ValueError, match="paper_only/report_only/readonly"):
            input_row(**kwargs)

    summary = report((input_row(),))
    for guarded in (
        config(),
        input_row(),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    ):
        for flag in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match="paper_only/report_only/readonly"):
                replace(guarded, **{flag: False})


def test_philly_fed_manual_constructors_reject_inconsistent_state() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_philly_fed_surprise_digest_ready",
                "market_research_philly_fed_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="no_inputs is report-only"):
        replace(
            ready,
            reason_codes=("market_research_philly_fed_surprise_digest_no_inputs",),
        )
    with pytest.raises(ValueError, match="surprise_status"):
        replace(ready, surprise_status="blocked")
    with pytest.raises(ValueError, match="surprise_delta"):
        replace(ready, surprise_delta=d("9.999999"))
    with pytest.raises(ValueError, match="abs_surprise_points"):
        replace(ready, abs_surprise_points=d("9.999999"))
    with pytest.raises(ValueError, match="acknowledgement_lag_seconds"):
        replace(ready, acknowledgement_lag_seconds=d("999.000000"))
    with pytest.raises(ValueError, match="redacted_release_reference"):
        replace(ready, redacted_release_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_release_count"):
        replace(report((input_row(),)), ready_release_count=ZERO)
    with pytest.raises(ValueError, match="row release_age_seconds"):
        replace(
            report((input_row(),)),
            rows=(replace(ready, release_age_seconds=d("999.000000")),),
        )
    two_row_report = report(
        (
            input_row("research.philly_fed.z", release_key="philly_fed.z"),
            input_row(),
        ),
    )
    with pytest.raises(ValueError, match="rows"):
        replace(two_row_report, rows=tuple(reversed(two_row_report.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_philly_fed_surprise_digest.py",
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
    for forbidden_source_fragment in (
        "live trading",
        "durable store",
        "order placement",
        "wallet",
        "database",
        "auth",
    ):
        assert forbidden_source_fragment not in source.lower()


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
        "points",
        "ratio",
        "score",
        "index",
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
