from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_macro_cpi_revision_digest import (
    DEFAULT_MARKET_RESEARCH_MACRO_CPI_REVISION_DIGEST_CONFIG_VERSION,
    MarketResearchMacroCpiRevisionDigestConfig,
    MarketResearchMacroCpiRevisionDigestInputRow,
    MarketResearchMacroCpiRevisionDigestReasonCodeCount,
    MarketResearchMacroCpiRevisionDigestReport,
    MarketResearchMacroCpiRevisionDigestRow,
    build_market_research_macro_cpi_revision_digest,
    market_research_macro_cpi_revision_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)
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


def config(**overrides: object) -> MarketResearchMacroCpiRevisionDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_MACRO_CPI_REVISION_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("7200.000000"),
        "material_revision_threshold": d("0.100000"),
        "min_source_count": d("2"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchMacroCpiRevisionDigestConfig(**values)


def input_row(
    research_key: str = "research.cpi.headline",
    *,
    condition_id: str = "condition_cpi_headline",
    cpi_series_key: str = "cpi.headline.yoy",
    cpi_release_reference: str = "public-bls-cpi-release",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3"),
    initial_value: Decimal = d("3.200000"),
    revised_value: Decimal = d("3.240000"),
    prior_value: Decimal = d("3.000000"),
    market_probability_before: Decimal = d("0.480000"),
    market_probability_after: Decimal = d("0.520000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchMacroCpiRevisionDigestInputRow:
    return MarketResearchMacroCpiRevisionDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        cpi_series_key=cpi_series_key,
        cpi_release_reference=cpi_release_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=30),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=20)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        initial_value=initial_value,
        revised_value=revised_value,
        prior_value=prior_value,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchMacroCpiRevisionDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchMacroCpiRevisionDigestReport:
    return build_market_research_macro_cpi_revision_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_cpi_revision_digest_reduces_rows_redacts_refs_and_sorts_deterministically() -> None:
    summary = report(
        (
            input_row(
                "research.cpi.core",
                condition_id="condition_cpi_core",
                cpi_series_key="cpi.core.mom",
                cpi_release_reference="https://vendor.example/cpi?token=secret-123",
                released_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=100),
                source_count=d("1"),
                initial_value=d("0.200000"),
                revised_value=d("0.350000"),
                prior_value=d("0.100000"),
                market_probability_before=d("0.420000"),
                market_probability_after=d("0.610000"),
            ),
            input_row(
                "research.cpi.shelter",
                condition_id="condition_cpi_shelter",
                cpi_series_key="cpi.shelter.mom",
                cpi_release_reference="private-cpi-feed",
                released_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=None,
                source_count=d("2"),
                initial_value=d("0.400000"),
                revised_value=d("0.550000"),
                prior_value=d("0.350000"),
                market_probability_before=d("0.300000"),
                market_probability_after=d("0.340000"),
            ),
            input_row(
                "research.cpi.headline",
                condition_id="condition_cpi_headline",
                cpi_series_key="cpi.headline.yoy",
                cpi_release_reference="public-bls-cpi-release",
                released_at=GENERATED_AT - timedelta(minutes=45),
                acknowledged_at=GENERATED_AT - timedelta(minutes=35),
                source_count=d("3"),
                initial_value=d("3.200000"),
                revised_value=d("3.240000"),
                prior_value=d("3.000000"),
                market_probability_before=d("0.480000"),
                market_probability_after=d("0.520000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_MACRO_CPI_REVISION_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_macro_cpi_revision_digest"
    )
    assert summary.cpi_release_count == d("3")
    assert summary.ready_release_count == d("1")
    assert summary.watch_release_count == d("1")
    assert summary.blocked_release_count == d("1")
    assert summary.material_revision_count == d("2")
    assert summary.stale_release_count == d("2")
    assert summary.thin_source_count == d("1")
    assert summary.missing_acknowledgement_count == d("1")
    assert summary.slow_acknowledgement_count == d("1")
    assert summary.probability_repricing_count == d("1")
    assert summary.average_revision_abs == d("0.113333")
    assert summary.max_release_age_seconds == d("14400.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.cpi_series_key, row.research_key) for row in summary.rows) == (
        ("cpi.shelter.mom", "research.cpi.shelter"),
        ("cpi.core.mom", "research.cpi.core"),
        ("cpi.headline.yoy", "research.cpi.headline"),
    )

    shelter = summary.rows[0]
    assert shelter.revision_status == "blocked"
    assert shelter.release_age_seconds == d("14400.000000")
    assert shelter.acknowledgement_lag_seconds is None
    assert shelter.revision_delta == d("0.150000")
    assert shelter.revision_abs == d("0.150000")
    assert shelter.probability_delta == d("0.040000")
    assert shelter.redacted_cpi_release_reference == "sha256:7a023c0f8002"
    assert shelter.reason_codes == (
        "market_research_macro_cpi_revision_digest_material_revision",
        "market_research_macro_cpi_revision_digest_missing_acknowledgement",
        "market_research_macro_cpi_revision_digest_stale_release",
    )

    core = summary.rows[1]
    assert core.revision_status == "watch"
    assert core.release_age_seconds == d("10800.000000")
    assert core.acknowledgement_lag_seconds == d("4800.000000")
    assert core.revision_delta == d("0.150000")
    assert core.probability_delta == d("0.190000")
    assert core.redacted_cpi_release_reference == "sha256:f833b9529a6b"
    assert core.reason_codes == (
        "market_research_macro_cpi_revision_digest_material_revision",
        "market_research_macro_cpi_revision_digest_probability_repricing",
        "market_research_macro_cpi_revision_digest_slow_acknowledgement",
        "market_research_macro_cpi_revision_digest_stale_release",
        "market_research_macro_cpi_revision_digest_thin_sources",
    )

    headline = summary.rows[2]
    assert headline.revision_status == "ready"
    assert headline.release_age_seconds == d("2700.000000")
    assert headline.acknowledgement_lag_seconds == d("600.000000")
    assert headline.revision_delta == d("0.040000")
    assert headline.revision_abs == d("0.040000")
    assert headline.probability_delta == d("0.040000")
    assert headline.redacted_cpi_release_reference == "public-bls-cpi-release"
    assert headline.reason_codes == (
        "market_research_macro_cpi_revision_digest_ready",
    )


    assert summary.reason_code_counts == (
        MarketResearchMacroCpiRevisionDigestReasonCodeCount(
            reason_code="market_research_macro_cpi_revision_digest_material_revision",
            count=d("2"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchMacroCpiRevisionDigestReasonCodeCount(
            reason_code="market_research_macro_cpi_revision_digest_stale_release",
            count=d("2"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchMacroCpiRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_macro_cpi_revision_digest_probability_repricing"
            ),
            count=d("1"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchMacroCpiRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_macro_cpi_revision_digest_missing_acknowledgement"
            ),
            count=d("1"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchMacroCpiRevisionDigestReasonCodeCount(
            reason_code="market_research_macro_cpi_revision_digest_ready",
            count=d("1"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchMacroCpiRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_macro_cpi_revision_digest_slow_acknowledgement"
            ),
            count=d("1"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchMacroCpiRevisionDigestReasonCodeCount(
            reason_code="market_research_macro_cpi_revision_digest_thin_sources",
            count=d("1"),
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
        "private-cpi-feed",
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


def test_cpi_revision_digest_allows_operational_words_in_public_identifiers() -> None:
    summary = report(
        (
            input_row(
                "research.cpi.database-source",
                condition_id="condition-cpi-submit-window",
                cpi_series_key="cpi.persistent.revision",
                cpi_release_reference="public-bls-cpi-release",
                released_at=GENERATED_AT - timedelta(minutes=45),
                acknowledged_at=GENERATED_AT - timedelta(minutes=30),
                source_count=d("3"),
                initial_value=d("3.200000"),
                revised_value=d("3.240000"),
                prior_value=d("3.100000"),
                market_probability_before=d("0.480000"),
                market_probability_after=d("0.520000"),
            ),
        ),
    )

    assert summary.rows[0].research_key == "research.cpi.database-source"
    assert summary.rows[0].condition_id == "condition-cpi-submit-window"
    assert summary.rows[0].cpi_series_key == "cpi.persistent.revision"


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    (
        ("research_key", "research.cpi.wallet-token"),
        ("condition_id", "condition-cpi-auth-private"),
        ("cpi_series_key", "https://credential.example/cpi"),
    ),
)
def test_cpi_revision_digest_rejects_sensitive_public_identifiers(
    field_name: str,
    unsafe_value: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        if field_name == "research_key":
            input_row(unsafe_value)
        else:
            input_row(**{field_name: unsafe_value})

    ready = report((input_row(),)).rows[0]
    with pytest.raises(ValueError, match=field_name):
        replace(ready, **{field_name: unsafe_value})


def test_cpi_revision_digest_payload_redacts_url_like_release_reference() -> None:
    summary = report(
        (
            input_row(
                cpi_release_reference="public-bls-cpi-release?release_id=2026-07",
            ),
        ),
    )

    payload = market_research_macro_cpi_revision_digest_payload(summary)
    public_payload = repr(payload).lower()

    assert "public-bls-cpi-release?release_id=2026-07" not in public_payload
    assert "?" not in public_payload
    assert payload["rows"][0]["redacted_cpi_release_reference"].startswith("sha256:")


def test_cpi_revision_digest_is_independent_of_ambient_decimal_context() -> None:
    with localcontext(Context(prec=1, rounding=ROUND_HALF_EVEN)):
        summary = report(
            (
                input_row(
                    "research.cpi.core",
                    condition_id="condition_cpi_core",
                    cpi_series_key="cpi.core.mom",
                    released_at=GENERATED_AT - timedelta(hours=3),
                    source_count=d("1"),
                    initial_value=d("0.200000"),
                    revised_value=d("0.350000"),
                    prior_value=d("0.100000"),
                ),
                input_row(
                    "research.cpi.shelter",
                    condition_id="condition_cpi_shelter",
                    cpi_series_key="cpi.shelter.mom",
                    released_at=GENERATED_AT - timedelta(hours=4),
                    source_count=d("2"),
                    initial_value=d("0.400000"),
                    revised_value=d("0.550000"),
                    prior_value=d("0.350000"),
                ),
                input_row(
                    source_count=d("3"),
                    initial_value=d("3.200000"),
                    revised_value=d("3.240000"),
                    prior_value=d("3.000000"),
                ),
            ),
        )

    assert summary.average_revision_abs == d("0.113333")
    assert summary.average_source_count == d("2.000000")
    assert summary.max_release_age_seconds == d("14400.000000")
    headline = next(row for row in summary.rows if row.cpi_series_key == "cpi.headline.yoy")
    assert headline.revision_delta == d("0.040000")
    assert headline.prior_delta == d("0.240000")


def test_cpi_revision_digest_canonicalizes_signed_zero() -> None:
    source = input_row(
        initial_value=d("-0.0000004"),
        revised_value=d("0.0000000"),
        prior_value=d("-0.0000004"),
    )

    summary = report((source,))
    payload = market_research_macro_cpi_revision_digest_payload(summary)

    assert source.initial_value == ZERO
    assert source.initial_value.is_signed() is False
    assert "-0.000000" not in repr(payload)


def test_empty_cpi_revision_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_macro_cpi_revision_digest"
    )
    assert summary.cpi_release_count == ZERO
    assert summary.ready_release_count == ZERO
    assert summary.watch_release_count == ZERO
    assert summary.blocked_release_count == ZERO
    assert summary.average_revision_abs == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchMacroCpiRevisionDigestReasonCodeCount(
            reason_code="market_research_macro_cpi_revision_digest_no_inputs",
            count=d("1.000000"),
            release_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_macro_cpi_revision_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_cpi_revision_digest_payload_uses_decimal_strings_and_omits_sensitive_refs() -> None:
    summary = report((input_row(),))
    payload = market_research_macro_cpi_revision_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["cpi_release_count"] == "1.000000"
    assert payload["average_revision_abs"] == "0.040000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'cpi_release_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_cpi_revision_digest_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchMacroCpiRevisionDigestConfig)
    assert is_dataclass(MarketResearchMacroCpiRevisionDigestInputRow)
    assert is_dataclass(MarketResearchMacroCpiRevisionDigestRow)
    assert is_dataclass(MarketResearchMacroCpiRevisionDigestReasonCodeCount)
    assert is_dataclass(MarketResearchMacroCpiRevisionDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("cpi-revision-v0"))
    with pytest.raises(ValueError, match="fresh_release_max_age_seconds"):
        config(fresh_release_max_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="material_revision_threshold"):
        config(material_revision_threshold=Decimal("NaN"))
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.5"))
    with pytest.raises(ValueError, match="max_acknowledgement_lag_seconds"):
        config(max_acknowledgement_lag_seconds=_DecimalSubclass("1800"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id=" bad")
    with pytest.raises(ValueError, match="released_at"):
        input_row(released_at=datetime(2026, 7, 3, 14, 0))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(acknowledged_at=_DateTimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="initial_value"):
        input_row(initial_value=Decimal("Infinity"))
    with pytest.raises(ValueError, match="revised_value"):
        input_row(revised_value=_DecimalSubclass("3.250000"))
    with pytest.raises(ValueError, match="market_probability_before"):
        input_row(market_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="market_probability_after"):
        input_row(market_probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_macro_cpi_revision_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_macro_cpi_revision_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_report_and_row_consistency_rejects_incoherent_manual_constructors() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_macro_cpi_revision_digest_ready",
                "market_research_macro_cpi_revision_digest_material_revision",
            ),
        )
    with pytest.raises(ValueError, match="revision_status"):
        replace(ready, revision_status="blocked")
    with pytest.raises(ValueError, match="revision_delta"):
        replace(ready, revision_delta=d("9.999999"))
    with pytest.raises(ValueError, match="revision_abs"):
        replace(ready, revision_abs=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_cpi_release_reference"):
        replace(ready, redacted_cpi_release_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_release_count"):
        replace(report((input_row(),)), ready_release_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.cpi.z", cpi_series_key="cpi.z"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_macro_cpi_revision_digest.py",
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
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float

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
    lowered_source = source.lower()
    assert "persist" not in lowered_source
    assert "database" not in lowered_source
    assert "advice" not in lowered_source
    assert "float(" not in lowered_source


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
        "source",
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
