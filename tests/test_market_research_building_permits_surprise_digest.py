from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_building_permits_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_BUILDING_PERMITS_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchBuildingPermitsSurpriseDigestConfig,
    MarketResearchBuildingPermitsSurpriseDigestInputRow,
    MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount,
    MarketResearchBuildingPermitsSurpriseDigestReport,
    MarketResearchBuildingPermitsSurpriseDigestRow,
    build_market_research_building_permits_surprise_digest,
    market_research_building_permits_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 15, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
SIX_DECIMAL_RE = re.compile(r"^-?\d+\.\d{6}$")
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
) -> MarketResearchBuildingPermitsSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_BUILDING_PERMITS_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_release_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_ratio": d("0.050000"),
        "max_revision_ratio": d("0.100000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchBuildingPermitsSurpriseDigestConfig(**values)


def input_row(
    research_key: str = "research.building_permits.headline",
    *,
    condition_id: str = "condition_building_permits_headline",
    market_slug: str = "us-building-permits-above-consensus",
    permit_release_key: str = "census.building_permits.headline",
    permit_region: str = "us",
    public_release_reference: str = "census-building-permits-calendar",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    forecast_permit_count: Decimal = d("1500000.000000"),
    actual_permit_count: Decimal = d("1530000.000000"),
    prior_permit_count: Decimal = d("1480000.000000"),
    revised_prior_permit_count: Decimal = d("1485000.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchBuildingPermitsSurpriseDigestInputRow:
    return MarketResearchBuildingPermitsSurpriseDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        permit_release_key=permit_release_key,
        permit_region=permit_region,
        public_release_reference=public_release_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=10)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        forecast_permit_count=forecast_permit_count,
        actual_permit_count=actual_permit_count,
        prior_permit_count=prior_permit_count,
        revised_prior_permit_count=revised_prior_permit_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchBuildingPermitsSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchBuildingPermitsSurpriseDigestReport:
    return build_market_research_building_permits_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_building_permits_surprise_digest_reduces_rows_and_sorts_deterministically() -> None:
    summary = report(
        (
            input_row(
                "research.building_permits.watch",
                condition_id="condition_watch_permits",
                market_slug="single-family-building-permits-miss",
                permit_release_key="census.building_permits.single_family",
                permit_region="single_family",
                released_at=GENERATED_AT - timedelta(minutes=55),
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                source_count=d("3.000000"),
                forecast_permit_count=d("900000.000000"),
                actual_permit_count=d("840000.000000"),
                prior_permit_count=d("880000.000000"),
                revised_prior_permit_count=d("980000.000000"),
            ),
            input_row(
                "research.building_permits.ready",
                condition_id="condition_ready_permits",
                market_slug="headline-building-permits-inline",
                permit_release_key="census.building_permits.headline",
                permit_region="headline",
                released_at=(GENERATED_AT - timedelta(minutes=30)).astimezone(
                    timezone(timedelta(hours=-4)),
                ),
                acknowledged_at=GENERATED_AT - timedelta(minutes=25),
                source_count=d("4.000000"),
                forecast_permit_count=d("1500000.000000"),
                actual_permit_count=d("1530000.000000"),
                prior_permit_count=d("1480000.000000"),
                revised_prior_permit_count=d("1485000.000000"),
            ),
            input_row(
                "research.building_permits.blocked",
                condition_id="condition_blocked_permits",
                market_slug="multi-family-building-permits-delay",
                permit_release_key="census.building_permits.multi_family",
                permit_region="multi_family",
                released_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=None,
                source_count=d("1.000000"),
                forecast_permit_count=d("600000.000000"),
                actual_permit_count=d("520000.000000"),
                prior_permit_count=d("610000.000000"),
                revised_prior_permit_count=d("590000.000000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=2))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_BUILDING_PERMITS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_building_permits_surprise_digest"
    )
    assert summary.permit_release_count == d("3.000000")
    assert summary.ready_release_count == d("1.000000")
    assert summary.watch_release_count == d("1.000000")
    assert summary.blocked_release_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.high_revision_count == d("1.000000")
    assert summary.stale_release_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.average_abs_surprise_ratio == d("0.073333")
    assert summary.max_abs_surprise_ratio == d("0.133333")
    assert summary.average_revision_ratio == d("0.049934")
    assert summary.average_source_count == d("2.666667")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.surprise_status, row.market_slug) for row in summary.rows) == (
        ("blocked", "multi-family-building-permits-delay"),
        ("watch", "single-family-building-permits-miss"),
        ("ready", "headline-building-permits-inline"),
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, MarketResearchBuildingPermitsSurpriseDigestRow)
    assert blocked.released_at == GENERATED_AT - timedelta(hours=4)
    assert blocked.acknowledgement_lag_seconds is None
    assert blocked.release_age_seconds == d("14400.000000")
    assert blocked.building_permits_surprise_count == d("-80000.000000")
    assert blocked.abs_surprise_ratio == d("0.133333")
    assert blocked.prior_revision_count == d("-20000.000000")
    assert blocked.revision_ratio == d("0.032787")
    assert blocked.reason_codes == (
        "market_research_building_permits_surprise_digest_material_surprise",
        "market_research_building_permits_surprise_digest_stale_release",
        "market_research_building_permits_surprise_digest_missing_acknowledgement",
        "market_research_building_permits_surprise_digest_thin_sources",
    )

    watched = summary.rows[1]
    assert watched.acknowledgement_lag_seconds == d("2100.000000")
    assert watched.building_permits_surprise_count == d("-60000.000000")
    assert watched.abs_surprise_ratio == d("0.066667")
    assert watched.prior_revision_count == d("100000.000000")
    assert watched.revision_ratio == d("0.113636")
    assert watched.reason_codes == (
        "market_research_building_permits_surprise_digest_material_surprise",
        "market_research_building_permits_surprise_digest_high_revision",
        "market_research_building_permits_surprise_digest_slow_acknowledgement",
    )

    ready = summary.rows[2]
    assert ready.released_at == GENERATED_AT - timedelta(minutes=30)
    assert ready.reason_codes == (
        "market_research_building_permits_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
            reason_code="market_research_building_permits_surprise_digest_material_surprise",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        ),
        MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
            reason_code="market_research_building_permits_surprise_digest_high_revision",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
            reason_code="market_research_building_permits_surprise_digest_stale_release",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_building_permits_surprise_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_building_permits_surprise_digest_"
                "slow_acknowledgement"
            ),
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
            reason_code="market_research_building_permits_surprise_digest_thin_sources",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
            reason_code="market_research_building_permits_surprise_digest_ready",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(item.reason_code for item in summary.reason_code_counts)


def test_empty_building_permits_surprise_digest_blocks_as_missing_evidence() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_building_permits_surprise_digest"
    )
    assert summary.permit_release_count == ZERO
    assert summary.ready_release_count == ZERO
    assert summary.watch_release_count == ZERO
    assert summary.blocked_release_count == ZERO
    assert summary.material_surprise_count == ZERO
    assert summary.high_revision_count == ZERO
    assert summary.stale_release_count == ZERO
    assert summary.thin_source_count == ZERO
    assert summary.missing_acknowledgement_count == ZERO
    assert summary.slow_acknowledgement_count == ZERO
    assert summary.average_abs_surprise_ratio == ZERO
    assert summary.max_abs_surprise_ratio == ZERO
    assert summary.average_revision_ratio == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_building_permits_surprise_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
            reason_code="market_research_building_permits_surprise_digest_no_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_uses_six_decimal_strings_and_no_raw_numeric_or_datetime_values() -> None:
    summary = report((input_row(),))
    payload = market_research_building_permits_surprise_digest_payload(summary)

    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["permit_release_count"] == "1.000000"
    assert payload["average_source_count"] == "3.000000"
    assert payload["rows"][0]["actual_permit_count"] == "1530000.000000"
    assert payload["rows"][0]["abs_surprise_ratio"] == "0.020000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "1.000000"
    assert isinstance(payload["rows"], list)
    assert isinstance(payload["reason_codes"], list)
    assert isinstance(payload["reason_code_counts"], list)
    assert_payload_is_plain_json(payload)
    assert_six_decimal_strings(payload)


def test_public_contracts_are_frozen_exact_type_decimal_only_and_reject_false_flags() -> None:
    summary = report((input_row(),))
    instances = (
        config(),
        input_row(),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    )
    for instance in instances:
        assert is_dataclass(instance)
        assert instance.__dataclass_params__.frozen
        assert_public_numeric_fields_are_exact_decimals(instance)

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]

    false_flag_cases = (
        lambda: config(paper_only=False),
        lambda: config(report_only=False),
        lambda: config(readonly=False),
        lambda: input_row(paper_only=False),
        lambda: input_row(report_only=False),
        lambda: input_row(readonly=False),
        lambda: replace(summary.rows[0], paper_only=False),
        lambda: replace(summary.rows[0], report_only=False),
        lambda: replace(summary.rows[0], readonly=False),
        lambda: replace(summary.reason_code_counts[0], paper_only=False),
        lambda: replace(summary.reason_code_counts[0], report_only=False),
        lambda: replace(summary.reason_code_counts[0], readonly=False),
        lambda: replace(summary, paper_only=False),
        lambda: replace(summary, report_only=False),
        lambda: replace(summary, readonly=False),
    )
    for make_value in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_value()


def test_validation_rejects_bad_inputs_timestamps_subclasses_and_unsafe_references() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("building-permits-surprise-v0"))
    with pytest.raises(ValueError, match="max_release_age_seconds"):
        config(max_release_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="material_surprise_ratio"):
        config(material_surprise_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="max_revision_ratio"):
        config(max_revision_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="max_acknowledgement_lag_seconds"):
        config(max_acknowledgement_lag_seconds=Decimal("NaN"))

    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="market_slug"):
        input_row(market_slug="bad slug")
    with pytest.raises(ValueError, match="permit_region"):
        input_row(permit_region="broker_feed")
    with pytest.raises(ValueError, match="public_release_reference"):
        input_row(public_release_reference="https://vendor.example/permits?token=value")
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
        input_row(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="forecast_permit_count"):
        input_row(forecast_permit_count=d("0.000000"))
    with pytest.raises(ValueError, match="actual_permit_count"):
        input_row(actual_permit_count=_DecimalSubclass("1530000.000000"))
    with pytest.raises(ValueError, match="prior_permit_count"):
        input_row(prior_permit_count=d("0.000000"))
    with pytest.raises(ValueError, match="revised_prior_permit_count"):
        input_row(revised_prior_permit_count=d("-1.000000"))
    with pytest.raises(ValueError, match="config"):
        build_market_research_building_permits_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_building_permits_surprise_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 15, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=datetime(2026, 7, 3, 15, 30, tzinfo=_MissingOffsetTimezone()))
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))
    with pytest.raises(ValueError, match="unique"):
        report((input_row("research.dupe"), input_row("research.dupe")))
    with pytest.raises(ValueError, match="released_at"):
        report((input_row(released_at=GENERATED_AT + timedelta(seconds=1)),))


def test_manual_public_constructors_reject_inconsistent_fields_and_noncanonical_sequences() -> None:
    ready_summary = report((input_row(),))
    ready = ready_summary.rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_building_permits_surprise_digest_ready",
                "market_research_building_permits_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_building_permits_surprise_digest_stale_release",
                "market_research_building_permits_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="surprise_status"):
        replace(ready, surprise_status="blocked")
    with pytest.raises(ValueError, match="building_permits_surprise_count"):
        replace(ready, building_permits_surprise_count=d("1.000000"))
    with pytest.raises(ValueError, match="abs_surprise_ratio"):
        replace(ready, abs_surprise_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="prior_revision_count"):
        replace(ready, prior_revision_count=d("1.000000"))
    with pytest.raises(ValueError, match="revision_ratio"):
        replace(ready, revision_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="acknowledgement_lag_seconds"):
        replace(ready, acknowledged_at=None)
    with pytest.raises(ValueError, match="acknowledgement_lag_seconds"):
        replace(ready, acknowledgement_lag_seconds=None)

    two_row_summary = report(
        (
            input_row(
                "research.z",
                permit_release_key="census.building_permits.z",
                actual_permit_count=d("1600000.000000"),
            ),
            input_row("research.a", permit_release_key="census.building_permits.a"),
        ),
    )
    with pytest.raises(ValueError, match="rows"):
        replace(two_row_summary, rows=tuple(reversed(two_row_summary.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            two_row_summary,
            reason_code_counts=tuple(reversed(two_row_summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(two_row_summary, reason_codes=tuple(reversed(two_row_summary.reason_codes)))
    with pytest.raises(ValueError, match="ready_release_count"):
        replace(ready_summary, ready_release_count=ZERO)


def test_module_has_no_io_secret_or_live_mutation_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_building_permits_surprise_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()
    lowered_report = repr(asdict(report((input_row(),)))).lower()

    forbidden_fragments = (
        "api_key",
        "auth",
        "broker",
        "cancel_order",
        "database",
        "exchange",
        "live_trading",
        "place_order",
        "private_key",
        "replace_order",
        "secret",
        "submit_order",
        "token",
        "trade",
        "wallet",
        "wallet_address",
    )
    assert not any(fragment in lowered_source for fragment in forbidden_fragments)
    assert not any(fragment in lowered_report for fragment in forbidden_fragments)

    imported_roots: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            leaf = call_leaf_name(node.func)
            if leaf is not None:
                call_names.append(leaf)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    assert imported_roots.isdisjoint(
        {
            "aiohttp",
            "ccxt",
            "eth_account",
            "httpx",
            "psycopg",
            "requests",
            "socket",
            "sqlalchemy",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
            "web3",
        },
    )
    assert not (
        set(call_names)
        & {
            "close",
            "commit",
            "connect",
            "cursor",
            "environ",
            "execute",
            "executemany",
            "getenv",
            "open",
            "rollback",
            "send",
            "urlopen",
            "write",
        }
    )
    assert not (
        set(attribute_names)
        & {
            "close",
            "commit",
            "connect",
            "cursor",
            "environ",
            "execute",
            "executemany",
            "getenv",
            "rollback",
            "send",
            "write",
        }
    )

    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_building_permits_surprise_digest.py"
    )
    assert source_path.name == "market_research_building_permits_surprise_digest.py"


def assert_payload_is_plain_json(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            assert_payload_is_plain_json(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_is_plain_json(child)
    else:
        assert not isinstance(value, (Decimal, datetime, float))
        assert type(value) is not int


def assert_six_decimal_strings(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if is_public_numeric_field(str(key)):
                assert type(child) is str, key
                assert SIX_DECIMAL_RE.fullmatch(child), (key, child)
            assert_six_decimal_strings(child)
    elif isinstance(value, list):
        for child in value:
            assert_six_decimal_strings(child)


def assert_public_numeric_fields_are_exact_decimals(value: object) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if is_public_numeric_field(field.name):
            if field_value is None:
                continue
            assert type(field_value) is Decimal, (field.name, field_value, type(field_value))
            assert field_value.as_tuple().exponent == -6, field.name


def is_public_numeric_field(field_name: str) -> bool:
    return field_name.endswith(
        (
            "_seconds",
            "_count",
            "_ratio",
        ),
    )


def call_leaf_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
