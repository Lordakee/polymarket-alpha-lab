from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, dataclass, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_calendar_catalyst_digest import (
    DEFAULT_MARKET_RESEARCH_CALENDAR_CATALYST_DIGEST_CONFIG_VERSION,
    MarketResearchCalendarCatalystDigestConfig,
    MarketResearchCalendarCatalystDigestInputRow,
    MarketResearchCalendarCatalystDigestReport,
    MarketResearchCalendarCatalystDigestRow,
    build_market_research_calendar_catalyst_digest,
    market_research_calendar_catalyst_digest_json,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


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


@dataclass(frozen=True)
class _ForeignPublicDataclass:
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchCalendarCatalystDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CALENDAR_CATALYST_DIGEST_CONFIG_VERSION
        ),
        "watch_within_seconds": d("86400.000000"),
        "stale_research_after_seconds": d("7200.000000"),
        "min_reference_count": d("2"),
    }
    values.update(overrides)
    return MarketResearchCalendarCatalystDigestConfig(**values)


def _row(
    catalyst_reference: str,
    *,
    market_research_key: str = "research.alpha",
    catalyst_key: str = "catalyst.alpha",
    catalyst_family: str = "earnings",
    catalyst_at: datetime | None = None,
    research_observed_at: datetime | None = None,
    reference_count: Decimal = d("2"),
    confidence_score: Decimal = d("0.750000"),
) -> MarketResearchCalendarCatalystDigestInputRow:
    return MarketResearchCalendarCatalystDigestInputRow(
        market_research_key=market_research_key,
        catalyst_key=catalyst_key,
        catalyst_family=catalyst_family,
        catalyst_reference=catalyst_reference,
        catalyst_at=catalyst_at or GENERATED_AT + timedelta(days=2),
        research_observed_at=research_observed_at or GENERATED_AT - timedelta(minutes=30),
        reference_count=reference_count,
        confidence_score=confidence_score,
    )


def test_calendar_catalyst_digest_reduces_to_report_rows_and_redacts_references() -> None:
    report = build_market_research_calendar_catalyst_digest(
        (
            _row(
                "https://calendar.example/earnings?token=secret-value",
                market_research_key="research.beta",
                catalyst_key="catalyst.beta",
                catalyst_family="macro",
                catalyst_at=GENERATED_AT + timedelta(hours=2),
                research_observed_at=GENERATED_AT - timedelta(minutes=15),
                reference_count=d("3"),
                confidence_score=d("0.900000"),
            ),
            _row(
                "vendor://research/private/path",
                market_research_key="research.beta",
                catalyst_key="catalyst.beta-later",
                catalyst_family="macro",
                catalyst_at=GENERATED_AT + timedelta(hours=30),
                research_observed_at=GENERATED_AT - timedelta(hours=3),
                reference_count=d("2"),
                confidence_score=d("0.700000"),
            ),
            _row(
                "public-news-digest",
                catalyst_key="catalyst.alpha-stale",
                catalyst_at=GENERATED_AT + timedelta(hours=4),
                research_observed_at=GENERATED_AT - timedelta(hours=4),
                reference_count=d("1"),
                confidence_score=d("0.500000"),
            ),
            _row(
                "resolved-calendar",
                market_research_key="research.gamma",
                catalyst_key="catalyst.gamma",
                catalyst_at=GENERATED_AT - timedelta(minutes=5),
                research_observed_at=GENERATED_AT - timedelta(minutes=20),
                reference_count=d("2"),
                confidence_score=d("0.800000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert isinstance(report, MarketResearchCalendarCatalystDigestReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_MARKET_RESEARCH_CALENDAR_CATALYST_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.catalyst_count == d("4")
    assert report.ready_catalyst_count == d("1")
    assert report.watch_catalyst_count == d("2")
    assert report.blocked_catalyst_count == d("1")
    assert report.upcoming_catalyst_count == d("3")
    assert report.elapsed_catalyst_count == d("1")
    assert report.stale_research_count == d("1")
    assert report.thin_reference_count == d("1")
    assert report.average_confidence_score == d("0.725000")
    assert report.ready_catalyst_ratio == d("0.250000")
    assert report.reason_codes == (
        "market_research_calendar_catalyst_digest_elapsed",
        "market_research_calendar_catalyst_digest_ready",
        "market_research_calendar_catalyst_digest_stale_research",
        "market_research_calendar_catalyst_digest_thin_references",
        "market_research_calendar_catalyst_digest_watch_window",
    )
    assert tuple(row.catalyst_key for row in report.rows) == (
        "catalyst.alpha-stale",
        "catalyst.beta",
        "catalyst.beta-later",
        "catalyst.gamma",
    )

    rows = {row.catalyst_key: row for row in report.rows}
    assert rows["catalyst.beta"] == MarketResearchCalendarCatalystDigestRow(
        market_research_key="research.beta",
        catalyst_key="catalyst.beta",
        catalyst_family="macro",
        catalyst_status="watch",
        seconds_until_catalyst=d("7200.000000"),
        research_age_seconds=d("900.000000"),
        watch_within_seconds=d("86400.000000"),
        stale_research_after_seconds=d("7200.000000"),
        reference_count=d("3"),
        reference_gap_count=d("0"),
        confidence_score=d("0.900000"),
        redacted_catalyst_reference="sha256:5921069c9acc",
        reason_codes=(
            "market_research_calendar_catalyst_digest_watch_window",
        ),
    )
    assert rows["catalyst.beta-later"].catalyst_status == "ready"
    assert rows["catalyst.alpha-stale"].catalyst_status == "watch"
    assert rows["catalyst.alpha-stale"].reason_codes == (
        "market_research_calendar_catalyst_digest_stale_research",
        "market_research_calendar_catalyst_digest_thin_references",
        "market_research_calendar_catalyst_digest_watch_window",
    )
    assert rows["catalyst.gamma"].catalyst_status == "blocked"
    assert rows["catalyst.gamma"].reason_codes == (
        "market_research_calendar_catalyst_digest_elapsed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    public = repr(asdict(report)).lower()
    for token in (
        "secret-value",
        "calendar.example",
        "vendor://",
        "private/path",
        "payload",
        "broker",
        "wallet",
        "account",
        "signing",
        "submit",
        "cancel",
        "secret",
        "token",
        "private",
    ):
        assert token not in public


def test_calendar_catalyst_digest_returns_ready_empty_report() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_calendar_catalyst_digest",
    )

    report = build_market_research_calendar_catalyst_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.catalyst_count == d("0")
    assert report.ready_catalyst_count == d("0")
    assert report.ready_catalyst_ratio == d("0.000000")
    assert report.average_confidence_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_calendar_catalyst_digest_no_inputs",
    )
    assert report.reason_code_counts == (
        module.MarketResearchCalendarCatalystDigestReasonCodeCount(
            reason_code="market_research_calendar_catalyst_digest_no_inputs",
            count=d("1.000000"),
            catalyst_ratio=d("0.000000"),
        ),
    )


def test_calendar_catalyst_digest_serializes_deterministically_without_public_numerics() -> None:
    rows = (
        _row(
            "calendar-two",
            catalyst_key="catalyst.two",
            catalyst_at=GENERATED_AT + timedelta(hours=3, microseconds=250000),
            research_observed_at=GENERATED_AT - timedelta(minutes=45, microseconds=500000),
            confidence_score=d("0.600000"),
        ),
        _row(
            "calendar-one",
            catalyst_key="catalyst.one",
            catalyst_at=GENERATED_AT + timedelta(hours=30),
            research_observed_at=GENERATED_AT - timedelta(minutes=30),
            confidence_score=d("0.900000"),
        ),
    )

    first = build_market_research_calendar_catalyst_digest(
        rows,
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=3))),
    )
    second = build_market_research_calendar_catalyst_digest(
        tuple(reversed(rows)),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    first_json = market_research_calendar_catalyst_digest_json(first)
    second_json = market_research_calendar_catalyst_digest_json(second)

    assert first_json == second_json
    assert first_json["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert first_json["catalyst_count"] == "2.000000"
    assert first_json["watch_catalyst_count"] == "1.000000"
    assert first_json["ready_catalyst_count"] == "1.000000"
    assert first_json["ready_catalyst_ratio"] == "0.500000"
    assert first_json["average_confidence_score"] == "0.750000"
    assert first_json["paper_only"] is True
    assert first_json["report_only"] is True
    assert first_json["readonly"] is True
    assert first_json["reason_codes"] == [
        "market_research_calendar_catalyst_digest_ready",
        "market_research_calendar_catalyst_digest_watch_window",
    ]
    assert first_json["reason_code_counts"] == [
        {
            "reason_code": "market_research_calendar_catalyst_digest_ready",
            "count": "1.000000",
            "catalyst_ratio": "0.500000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "market_research_calendar_catalyst_digest_watch_window",
            "count": "1.000000",
            "catalyst_ratio": "0.500000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]

    serialized_rows = first_json["rows"]
    assert isinstance(serialized_rows, list)
    assert [row["catalyst_key"] for row in serialized_rows] == [
        "catalyst.one",
        "catalyst.two",
    ]
    assert serialized_rows[0]["seconds_until_catalyst"] == "108000.000000"
    assert serialized_rows[1]["seconds_until_catalyst"] == "10800.250000"
    assert serialized_rows[1]["research_age_seconds"] == "2700.500000"
    assert serialized_rows[1]["reason_codes"] == [
        "market_research_calendar_catalyst_digest_watch_window",
    ]
    assert serialized_rows[1]["paper_only"] is True
    assert serialized_rows[1]["report_only"] is True
    assert serialized_rows[1]["readonly"] is True

    def walk(value: object) -> tuple[object, ...]:
        if isinstance(value, dict):
            return tuple(item for nested in value.values() for item in walk(nested))
        if isinstance(value, list):
            return tuple(item for nested in value for item in walk(nested))
        return (value,)

    assert not any(isinstance(value, Decimal) for value in walk(first_json))
    assert not any(type(value) is int for value in walk(first_json))
    assert not any(type(value) is float for value in walk(first_json))


def test_calendar_catalyst_digest_json_revalidates_nested_dataclass_rows() -> None:
    report = build_market_research_calendar_catalyst_digest(
        (_row("fresh"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report.rows[0], "catalyst_status", "blocked")

    with pytest.raises(ValueError, match="catalyst_status"):
        market_research_calendar_catalyst_digest_json(report)

    foreign_dataclass_report = build_market_research_calendar_catalyst_digest(
        (_row("foreign"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(
        foreign_dataclass_report,
        "rows",
        (_ForeignPublicDataclass(),),
    )
    with pytest.raises(ValueError, match="supported public dataclass"):
        market_research_calendar_catalyst_digest_json(foreign_dataclass_report)

    datetime_report = build_market_research_calendar_catalyst_digest(
        (_row("datetime"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(
        datetime_report,
        "generated_at",
        datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="UTC"):
        market_research_calendar_catalyst_digest_json(datetime_report)


def test_calendar_catalyst_digest_json_rejects_tampered_nested_flags() -> None:
    report = build_market_research_calendar_catalyst_digest(
        (_row("fresh"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report.rows[0], "paper_only", False)

    with pytest.raises(ValueError, match="paper_only"):
        market_research_calendar_catalyst_digest_json(report)


def test_calendar_catalyst_digest_json_rejects_raw_payload_bodies() -> None:
    report = build_market_research_calendar_catalyst_digest(
        (_row("fresh"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="MarketResearchCalendarCatalystDigestReport"):
        market_research_calendar_catalyst_digest_json(asdict(report))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="MarketResearchCalendarCatalystDigestReport"):
        market_research_calendar_catalyst_digest_json([report])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="MarketResearchCalendarCatalystDigestReport"):
        market_research_calendar_catalyst_digest_json({report})  # type: ignore[arg-type]


def test_calendar_catalyst_digest_json_rejects_non_six_decimal_payload_values() -> None:
    report = build_market_research_calendar_catalyst_digest(
        (_row("fresh"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report.rows[0], "seconds_until_catalyst", d("172800.0000001"))

    with pytest.raises(ValueError, match="six decimal"):
        market_research_calendar_catalyst_digest_json(report)


def test_calendar_catalyst_digest_json_ready_rejects_raw_collections_and_unknowns() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_calendar_catalyst_digest",
    )

    with pytest.raises(ValueError, match="raw collection"):
        module._json_ready([d("1.000000")])
    with pytest.raises(ValueError, match="raw collection"):
        module._json_ready({"catalyst_count": d("1.000000")})
    with pytest.raises(ValueError, match="raw collection"):
        module._json_ready({d("1.000000")})
    with pytest.raises(ValueError, match="supported public dataclass"):
        module._json_ready(_ForeignPublicDataclass())
    with pytest.raises(ValueError, match="six decimal"):
        module._json_ready(d("1.0000001"))


def test_calendar_catalyst_digest_validates_public_types_values_and_flags() -> None:
    with pytest.raises(ValueError, match="watch_within_seconds"):
        MarketResearchCalendarCatalystDigestConfig(watch_within_seconds=86400)
    with pytest.raises(ValueError, match="stale_research_after_seconds"):
        MarketResearchCalendarCatalystDigestConfig(
            stale_research_after_seconds=_DecimalSubclass("7200.000000"),
        )
    with pytest.raises(ValueError, match="min_reference_count"):
        MarketResearchCalendarCatalystDigestConfig(min_reference_count=d("1.5"))
    with pytest.raises(ValueError, match="watch_within_seconds"):
        MarketResearchCalendarCatalystDigestConfig(
            watch_within_seconds=Decimal("NaN"),
        )
    with pytest.raises(ValueError, match="config_version"):
        MarketResearchCalendarCatalystDigestConfig(
            config_version=_StringSubclass(
                DEFAULT_MARKET_RESEARCH_CALENDAR_CATALYST_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="supported config_version"):
        MarketResearchCalendarCatalystDigestConfig(config_version="calendar-catalyst-v1")
    with pytest.raises(ValueError, match="catalyst_reference"):
        _row("")
    with pytest.raises(ValueError, match="catalyst_family"):
        _row("unsafe", catalyst_family="wallet_feed")
    with pytest.raises(ValueError, match="catalyst_at"):
        _row("naive-catalyst", catalyst_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="catalyst_at"):
        _row(
            "none-offset-catalyst",
            catalyst_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="research_observed_at"):
        _row("naive-research", research_observed_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="research_observed_at"):
        build_market_research_calendar_catalyst_digest(
            (_row("future-research", research_observed_at=GENERATED_AT + timedelta(seconds=1)),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="reference_count"):
        _row("float-count", reference_count=2.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence_score"):
        _row("nonfinite-confidence", confidence_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_row("not-paper"), paper_only=False)
    with pytest.raises(ValueError, match="input rows"):
        build_market_research_calendar_catalyst_digest(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_market_research_calendar_catalyst_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_calendar_catalyst_digest(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )

    report = build_market_research_calendar_catalyst_digest(
        (_row("fresh"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.rows[0].catalyst_status = "blocked"


def test_calendar_catalyst_digest_reason_code_counts_are_canonical() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_calendar_catalyst_digest",
    )
    reason_count_type = module.MarketResearchCalendarCatalystDigestReasonCodeCount

    report = build_market_research_calendar_catalyst_digest(
        (
            _row(
                "ready-calendar",
                catalyst_key="catalyst.ready",
                catalyst_at=GENERATED_AT + timedelta(days=2),
            ),
            _row(
                "watch-calendar",
                catalyst_key="catalyst.watch",
                catalyst_at=GENERATED_AT + timedelta(hours=3),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.reason_code_counts == (
        reason_count_type(
            reason_code="market_research_calendar_catalyst_digest_ready",
            count=d("1.000000"),
            catalyst_ratio=d("0.500000"),
        ),
        reason_count_type(
            reason_code="market_research_calendar_catalyst_digest_watch_window",
            count=d("1.000000"),
            catalyst_ratio=d("0.500000"),
        ),
    )

    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        replace(
            report,
            reason_code_counts=tuple(reversed(report.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(report, reason_code_counts=report.reason_code_counts[:1])
    with pytest.raises(ValueError, match="count must be positive"):
        reason_count_type(
            reason_code="market_research_calendar_catalyst_digest_ready",
            count=d("0.000000"),
            catalyst_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="catalyst_ratio"):
        reason_count_type(
            reason_code="market_research_calendar_catalyst_digest_ready",
            count=d("1.000000"),
            catalyst_ratio=1,  # type: ignore[arg-type]
        )


def test_calendar_catalyst_digest_public_dataclasses_are_frozen() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_calendar_catalyst_digest",
    )
    report = build_market_research_calendar_catalyst_digest(
        (_row("fresh"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    values = (
        _config(),
        _row("input"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_calendar_catalyst_digest_public_dataclasses_reject_subclassing() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_calendar_catalyst_digest",
    )

    for public_type in (
        MarketResearchCalendarCatalystDigestConfig,
        MarketResearchCalendarCatalystDigestInputRow,
        MarketResearchCalendarCatalystDigestRow,
        module.MarketResearchCalendarCatalystDigestReasonCodeCount,
        MarketResearchCalendarCatalystDigestReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})


def test_calendar_catalyst_digest_scope_excludes_io_and_forbidden_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_calendar_catalyst_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    lowered_source = source.lower()
    for token in (
        "live",
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "order",
        "exchange",
        "trade",
        "account",
        "advice",
        "network",
        "database",
        "persist",
        "supabase",
        "file",
        "payload",
        "secret",
        "token",
        "private",
    ):
        assert token not in lowered_source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
