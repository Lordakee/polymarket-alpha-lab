from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_construction_spending_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_CONSTRUCTION_SPENDING_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchConstructionSpendingSurpriseDigestConfig,
    MarketResearchConstructionSpendingSurpriseDigestInputRow,
    MarketResearchConstructionSpendingSurpriseDigestReasonCodeCount,
    MarketResearchConstructionSpendingSurpriseDigestReport,
    MarketResearchConstructionSpendingSurpriseDigestRow,
    build_market_research_construction_spending_surprise_digest,
    market_research_construction_spending_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


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


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchConstructionSpendingSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CONSTRUCTION_SPENDING_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("7200.000000"),
        "min_source_count": d("2"),
        "material_surprise_threshold_amount": d("5000000000.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchConstructionSpendingSurpriseDigestConfig(**values)


def input_row(
    research_key: str = "research.construction.spending",
    *,
    condition_id: str = "condition_construction_spending",
    market_slug: str = "us-construction-spending-above-consensus",
    construction_report_key: str = "census.construction.spending",
    construction_report_family: str = "construction",
    construction_report_reference: str = "public-census-construction-calendar",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("2"),
    forecast_spending_amount: Decimal = d("2100000000000.000000"),
    actual_spending_amount: Decimal = d("2103000000000.000000"),
    surprise_score: Decimal = d("0.015000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchConstructionSpendingSurpriseDigestInputRow:
    return MarketResearchConstructionSpendingSurpriseDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        construction_report_key=construction_report_key,
        construction_report_family=construction_report_family,
        construction_report_reference=construction_report_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=10)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        forecast_spending_amount=forecast_spending_amount,
        actual_spending_amount=actual_spending_amount,
        surprise_score=surprise_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchConstructionSpendingSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchConstructionSpendingSurpriseDigestReport:
    return build_market_research_construction_spending_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_construction_spending_surprise_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.construction.private",
                condition_id="condition_private_construction",
                market_slug="private-construction-spending-miss",
                construction_report_key="census.construction.private",
                construction_report_family="private",
                construction_report_reference=(
                    "https://vendor.example/construction?token=secret-123"
                ),
                released_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=80),
                source_count=d("1"),
                forecast_spending_amount=d("1650000000000.000000"),
                actual_spending_amount=d("1639000000000.000000"),
                surprise_score=d("0.090000"),
            ),
            input_row(
                "research.construction.headline",
                condition_id="condition_headline_construction",
                market_slug="us-construction-spending-above-consensus",
                construction_report_key="census.construction.spending",
                construction_report_family="headline",
                construction_report_reference="public-census-construction-calendar",
                released_at=GENERATED_AT - timedelta(minutes=40),
                acknowledged_at=GENERATED_AT - timedelta(minutes=35),
                source_count=d("3"),
                forecast_spending_amount=d("2100000000000.000000"),
                actual_spending_amount=d("2103000000000.000000"),
                surprise_score=d("0.015000"),
            ),
            input_row(
                "research.construction.public",
                condition_id="condition_public_construction",
                market_slug="public-construction-spending-drop",
                construction_report_key="census.construction.public",
                construction_report_family="public",
                construction_report_reference="private-construction-feed",
                released_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=None,
                source_count=d("2"),
                forecast_spending_amount=d("475000000000.000000"),
                actual_spending_amount=d("468000000000.000000"),
                surprise_score=d("0.070000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_CONSTRUCTION_SPENDING_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_construction_spending_surprise_digest"
    )
    assert summary.construction_report_count == d("3.000000")
    assert summary.ready_report_count == d("1.000000")
    assert summary.watch_report_count == d("1.000000")
    assert summary.blocked_report_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_release_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.average_surprise_score == d("0.058333")
    assert summary.max_release_age_seconds == d("18000.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(
        (row.market_slug, row.construction_report_key) for row in summary.rows
    ) == (
        ("public-construction-spending-drop", "census.construction.public"),
        ("private-construction-spending-miss", "census.construction.private"),
        ("us-construction-spending-above-consensus", "census.construction.spending"),
    )

    public = summary.rows[0]
    assert public.surprise_status == "blocked"
    assert public.release_age_seconds == d("18000.000000")
    assert public.acknowledgement_lag_seconds is None
    assert public.construction_spending_surprise_amount == d("-7000000000.000000")
    assert public.redacted_construction_report_reference == "sha256:1a35e1f9be2c"
    assert public.reason_codes == (
        "market_research_construction_spending_surprise_digest_material_surprise",
        "market_research_construction_spending_surprise_digest_missing_acknowledgement",
        "market_research_construction_spending_surprise_digest_stale_release",
    )

    private = summary.rows[1]
    assert private.surprise_status == "watch"
    assert private.release_age_seconds == d("10800.000000")
    assert private.acknowledgement_lag_seconds == d("6000.000000")
    assert private.construction_spending_surprise_amount == d("-11000000000.000000")
    assert private.redacted_construction_report_reference == "sha256:de33d92fc270"
    assert private.reason_codes == (
        "market_research_construction_spending_surprise_digest_material_surprise",
        "market_research_construction_spending_surprise_digest_slow_acknowledgement",
        "market_research_construction_spending_surprise_digest_stale_release",
        "market_research_construction_spending_surprise_digest_thin_sources",
    )

    headline = summary.rows[2]
    assert headline.surprise_status == "ready"
    assert headline.release_age_seconds == d("2400.000000")
    assert headline.acknowledgement_lag_seconds == d("300.000000")
    assert headline.construction_spending_surprise_amount == d("3000000000.000000")
    assert headline.redacted_construction_report_reference == (
        "public-census-construction-calendar"
    )
    assert headline.reason_codes == (
        "market_research_construction_spending_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchConstructionSpendingSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_construction_spending_surprise_digest_"
                "material_surprise"
            ),
            count=d("2.000000"),
            report_ratio=d("0.666667"),
        ),
        MarketResearchConstructionSpendingSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_construction_spending_surprise_digest_stale_release"
            ),
            count=d("2.000000"),
            report_ratio=d("0.666667"),
        ),
        MarketResearchConstructionSpendingSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_construction_spending_surprise_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchConstructionSpendingSurpriseDigestReasonCodeCount(
            reason_code="market_research_construction_spending_surprise_digest_ready",
            count=d("1.000000"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchConstructionSpendingSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_construction_spending_surprise_digest_"
                "slow_acknowledgement"
            ),
            count=d("1.000000"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchConstructionSpendingSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_construction_spending_surprise_digest_thin_sources"
            ),
            count=d("1.000000"),
            report_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )

    serialized = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "private-construction-feed",
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
        "private-construction-feed",
    ):
        assert token not in serialized


def test_empty_construction_spending_surprise_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_construction_spending_surprise_digest"
    )
    assert summary.construction_report_count == ZERO
    assert summary.ready_report_count == ZERO
    assert summary.watch_report_count == ZERO
    assert summary.blocked_report_count == ZERO
    assert summary.average_surprise_score == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchConstructionSpendingSurpriseDigestReasonCodeCount(
            reason_code="market_research_construction_spending_surprise_digest_no_inputs",
            count=d("1.000000"),
            report_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_construction_spending_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_uses_decimal_strings_and_omits_raw_refs() -> None:
    summary = report((input_row(),))
    payload = market_research_construction_spending_surprise_digest_payload(summary)

    assert isinstance(payload["rows"], list)
    assert isinstance(payload["reason_code_counts"], list)
    assert isinstance(payload["reason_codes"], list)
    assert isinstance(payload["rows"][0]["reason_codes"], list)
    assert payload["construction_report_count"] == "1.000000"
    assert payload["average_surprise_score"] == "0.015000"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'construction_report_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_equal_ranked_rows_use_stable_identity_tiebreakers() -> None:
    summary = report(
        (
            input_row(
                "research.construction.z",
                condition_id="condition_z",
                market_slug="same-construction-market",
                construction_report_key="census.construction.same",
            ),
            input_row(
                "research.construction.a",
                condition_id="condition_a",
                market_slug="same-construction-market",
                construction_report_key="census.construction.same",
            ),
        ),
    )

    assert tuple(row.condition_id for row in summary.rows) == (
        "condition_a",
        "condition_z",
    )
    assert tuple(row.research_key for row in summary.rows) == (
        "research.construction.a",
        "research.construction.z",
    )


def test_validates_public_contracts_decimal_fields_and_flags() -> None:
    assert is_dataclass(MarketResearchConstructionSpendingSurpriseDigestConfig)
    assert is_dataclass(MarketResearchConstructionSpendingSurpriseDigestInputRow)
    assert is_dataclass(MarketResearchConstructionSpendingSurpriseDigestRow)
    assert is_dataclass(MarketResearchConstructionSpendingSurpriseDigestReasonCodeCount)
    assert is_dataclass(MarketResearchConstructionSpendingSurpriseDigestReport)

    summary = report((input_row(),))
    for value in (
        config(),
        input_row(),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    ):
        assert_decimal_numeric_fields(value)

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("3.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("construction-spending-surprise-v0"))
    with pytest.raises(ValueError, match="fresh_release_max_age_seconds"):
        config(fresh_release_max_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.5"))
    with pytest.raises(ValueError, match="material_surprise_threshold_amount"):
        config(material_surprise_threshold_amount=_DecimalSubclass("5000000000"))
    with pytest.raises(ValueError, match="max_acknowledgement_lag_seconds"):
        config(max_acknowledgement_lag_seconds=Decimal("NaN"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="market_slug"):
        input_row(market_slug="bad slug")
    with pytest.raises(ValueError, match="construction_report_family"):
        input_row(construction_report_family="broker_feed")
    with pytest.raises(ValueError, match="released_at"):
        input_row(released_at=datetime(2026, 7, 3, 15, 0))
    with pytest.raises(ValueError, match="released_at"):
        input_row(
            released_at=datetime(
                2026,
                7,
                3,
                15,
                0,
                tzinfo=_MissingOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(acknowledged_at=_DatetimeSubclass(2026, 7, 3, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_spending_amount"):
        input_row(forecast_spending_amount=Decimal("Infinity"))
    with pytest.raises(ValueError, match="actual_spending_amount"):
        input_row(actual_spending_amount=_DecimalSubclass("2103000000000.000000"))
    with pytest.raises(ValueError, match="surprise_score"):
        input_row(surprise_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_construction_spending_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_construction_spending_surprise_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_report_and_row_consistency_rejects_incoherent_manual_constructors() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_construction_spending_surprise_digest_ready",
                "market_research_construction_spending_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="surprise_status"):
        replace(ready, surprise_status="blocked")
    with pytest.raises(ValueError, match="construction_spending_surprise_amount"):
        replace(ready, construction_spending_surprise_amount=d("9.999999"))
    with pytest.raises(ValueError, match="acknowledgement_lag_seconds"):
        replace(ready, acknowledged_at=None)
    with pytest.raises(ValueError, match="acknowledgement_lag_seconds"):
        replace(ready, acknowledgement_lag_seconds=None)
    with pytest.raises(ValueError, match="acknowledgement_lag_seconds"):
        replace(ready, acknowledgement_lag_seconds=d("1.000000"))
    with pytest.raises(ValueError, match="redacted_construction_report_reference"):
        replace(ready, redacted_construction_report_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_report_count"):
        replace(report((input_row(),)), ready_report_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        two_row_report = report(
            (
                input_row(
                    "research.construction.z",
                    construction_report_key="census.construction.z",
                ),
                input_row(),
            ),
        )
        replace(two_row_report, rows=tuple(reversed(two_row_report.rows)))


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_construction_spending_surprise_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    serialized_source = source.lower()
    serialized_report = repr(
        asdict(
            build_market_research_construction_spending_surprise_digest(
                (input_row(),),
                config=config(),
                generated_at=GENERATED_AT,
            ),
        ),
    ).lower()

    forbidden_literals = (
        "auth",
        "buy",
        "database",
        "db",
        "execute",
        "live",
        "order",
        "persist",
        "sell",
        "store",
        "trade",
        "wallet",
    )
    assert not any(token in serialized_report for token in forbidden_literals)
    assert not any(token in serialized_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "supabase",
        "urllib",
    )
    forbidden_call_or_attribute_names = {
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "open",
        "persist",
        "rollback",
        "send",
        "write",
    }
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_call_or_attribute_names)
    assert not (set(attribute_names) & forbidden_call_or_attribute_names)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "amount",
        "count",
        "lag",
        "ratio",
        "score",
        "threshold",
    )
    for field in fields(value):
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            if field_value is None:
                continue
            assert type(field_value) is Decimal, field.name
