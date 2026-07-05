from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
SIX_DECIMAL_RE = re.compile(r"^-?\d+\.\d{6}$")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_existing_home_sales_surprise_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def decimal_arg(value: str | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else d(value)


def observation(
    source_id: str,
    *,
    region_id: str = "us",
    market_slug: str = "existing-home-sales-above-consensus",
    observed_sales: str | Decimal = "4210000.000000",
    expected_sales: str | Decimal = "4100000.000000",
    surprise_ratio: str | Decimal = "0.026829",
    source_row_count: str | Decimal = "2",
    data_timestamp: datetime = datetime(2026, 7, 3, 11, 30, tzinfo=UTC),
    reason_codes: tuple[str, ...] = ("existing_home_sales_positive_surprise",),
):
    digest = api()
    return digest.ExistingHomeSalesSurpriseObservation(
        source_id=source_id,
        region_id=region_id,
        market_slug=market_slug,
        observed_sales=decimal_arg(observed_sales),
        expected_sales=decimal_arg(expected_sales),
        surprise_ratio=decimal_arg(surprise_ratio),
        source_row_count=decimal_arg(source_row_count),
        data_timestamp=data_timestamp,
        reason_codes=reason_codes,
    )


def report(*rows):
    digest = api()
    return digest.build_market_research_existing_home_sales_surprise_digest(
        rows,
        config=digest.ExistingHomeSalesSurpriseDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_digest_reduces_existing_home_sales_surprises_with_deterministic_rows() -> None:
    digest_report = report(
        observation(
            "source-inline",
            region_id="midwest",
            market_slug="midwest-existing-home-sales-inline",
            observed_sales="990000.000000",
            expected_sales="1000000.000000",
            surprise_ratio="-0.010000",
            source_row_count="1",
            data_timestamp=datetime(2026, 7, 3, 8, 15, tzinfo=timezone(timedelta(hours=-4))),
            reason_codes=("existing_home_sales_inline",),
        ),
        observation(
            "source-blocked",
            region_id="west",
            market_slug="west-existing-home-sales-spike",
            observed_sales="1120000.000000",
            expected_sales="1000000.000000",
            surprise_ratio="0.120000",
            source_row_count="3",
            data_timestamp=datetime(2026, 7, 3, 12, 45, tzinfo=UTC),
            reason_codes=("existing_home_sales_positive_surprise",),
        ),
        observation(
            "source-watch",
            region_id="south",
            market_slug="south-existing-home-sales-miss",
            observed_sales="1880000.000000",
            expected_sales="2000000.000000",
            surprise_ratio="-0.060000",
            source_row_count="2",
            data_timestamp=datetime(2026, 7, 3, 11, 30, tzinfo=UTC),
            reason_codes=("existing_home_sales_negative_surprise",),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-existing-home-sales-surprise-digest-v0"
    )
    assert digest_report.source_row_count == d("6")
    assert digest_report.observation_count == d("3")
    assert digest_report.positive_surprise_count == d("1")
    assert digest_report.negative_surprise_count == d("1")
    assert digest_report.inline_count == d("1")
    assert digest_report.max_abs_surprise_ratio == d("0.120000")
    assert digest_report.average_surprise_ratio == d("0.016667")
    assert digest_report.blocked_observation_ratio == d("0.333333")
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_existing_home_sales_surprise_digest"
    )
    assert digest_report.reason_codes == (
        "existing_home_sales_large_surprise_present",
        "existing_home_sales_mixed_surprises_present",
    )
    assert digest_report.reason_code_counts == (
        api().ExistingHomeSalesSurpriseReasonCodeCount(
            reason_code="existing_home_sales_large_surprise_present",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        api().ExistingHomeSalesSurpriseReasonCodeCount(
            reason_code="existing_home_sales_mixed_surprises_present",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.market_slug for row in digest_report.surprise_rows) == (
        "west-existing-home-sales-spike",
        "south-existing-home-sales-miss",
        "midwest-existing-home-sales-inline",
    )
    assert digest_report.surprise_rows[0].region_id == "west"
    assert digest_report.surprise_rows[0].surprise_direction == "positive"
    assert digest_report.surprise_rows[0].surprise_status == "blocked"
    assert digest_report.surprise_rows[0].reason_codes == (
        "existing_home_sales_segment_large_positive_surprise",
    )
    assert digest_report.surprise_rows[0].data_timestamp == datetime(
        2026,
        7,
        3,
        12,
        45,
        tzinfo=UTC,
    )
    assert digest_report.surprise_rows[1].surprise_direction == "negative"
    assert digest_report.surprise_rows[1].surprise_status == "watch"
    assert digest_report.surprise_rows[1].reason_codes == (
        "existing_home_sales_segment_negative_surprise",
    )
    assert digest_report.surprise_rows[2].surprise_direction == "inline"
    assert digest_report.surprise_rows[2].surprise_status == "pass"


def test_empty_digest_is_readonly_and_decimal_zeroed() -> None:
    digest_report = report()

    assert digest_report.source_row_count == d("0")
    assert digest_report.observation_count == d("0")
    assert digest_report.positive_surprise_count == d("0")
    assert digest_report.negative_surprise_count == d("0")
    assert digest_report.inline_count == d("0")
    assert digest_report.max_abs_surprise_ratio == d("0.000000")
    assert digest_report.average_surprise_ratio == d("0.000000")
    assert digest_report.blocked_observation_ratio == d("0.000000")
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_existing_home_sales_surprise_digest"
    )
    assert digest_report.reason_codes == ("existing_home_sales_surprise_digest_empty",)
    assert digest_report.reason_code_counts == (
        api().ExistingHomeSalesSurpriseReasonCodeCount(
            reason_code="existing_home_sales_surprise_digest_empty",
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert digest_report.surprise_rows == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_digest_rejects_float_inputs_false_flags_duplicates_and_mutation() -> None:
    digest = api()

    with pytest.raises(ValueError, match="observed_sales must be a Decimal"):
        digest.ExistingHomeSalesSurpriseObservation(
            source_id="source-float",
            region_id="us",
            market_slug="existing-home-sales-float",
            observed_sales=4210000.0,
            expected_sales=d("4100000.000000"),
            surprise_ratio=d("0.026829"),
            source_row_count=d("1"),
            data_timestamp=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
            reason_codes=("existing_home_sales_positive_surprise",),
        )
    with pytest.raises(ValueError, match="observed_sales must be a Decimal"):
        observation("source-decimal-subclass", observed_sales=_DecimalSubclass("4210000"))
    with pytest.raises(ValueError, match="expected_sales must be positive"):
        observation("source-zero-expected", expected_sales="0.000000")
    with pytest.raises(ValueError, match="source_row_count must be an integer Decimal"):
        observation("source-fractional-count", source_row_count="1.500000")

    row = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.observed_sales = d("200")  # type: ignore[misc]

    with pytest.raises(ValueError, match="observation paper_only must be True"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="observation readonly must be True"):
        replace(row, readonly=False)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        digest.ExistingHomeSalesSurpriseDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="config report_only must be True"):
        digest.ExistingHomeSalesSurpriseDigestConfig(report_only=False)
    with pytest.raises(ValueError, match="config readonly must be True"):
        digest.ExistingHomeSalesSurpriseDigestConfig(readonly=False)

    digest_report = report(observation("source-flags"))
    with pytest.raises(ValueError, match="row paper_only must be True"):
        replace(digest_report.surprise_rows[0], paper_only=False)
    with pytest.raises(ValueError, match="row report_only must be True"):
        replace(digest_report.surprise_rows[0], report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.surprise_rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)
    with pytest.raises(ValueError, match="report report_only must be True"):
        replace(digest_report, report_only=False)
    with pytest.raises(ValueError, match="report readonly must be True"):
        replace(digest_report, readonly=False)

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")


def test_digest_validates_timestamp_reason_codes_and_surprise_math() -> None:
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(
            "source-naive",
            data_timestamp=datetime(2026, 7, 3, 12, 0),
        )
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(
            "source-missing-offset",
            data_timestamp=datetime(2026, 7, 3, 12, 0, tzinfo=_MissingOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api().build_market_research_existing_home_sales_surprise_digest(
            (),
            config=api().ExistingHomeSalesSurpriseDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 16, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="reason_codes must match surprise direction"):
        observation(
            "source-bad-reason",
            observed_sales="4210000.000000",
            expected_sales="4100000.000000",
            surprise_ratio="0.026829",
            reason_codes=("existing_home_sales_negative_surprise",),
        )

    with pytest.raises(ValueError, match="surprise_ratio must match observed and expected"):
        observation(
            "source-bad-math",
            observed_sales="4210000.000000",
            expected_sales="4100000.000000",
            surprise_ratio="0.010000",
        )


def test_manual_report_and_row_consistency_rejects_drift() -> None:
    digest = api()
    digest_report = report(
        observation(
            "source-blocked-consistency",
            observed_sales="1120000.000000",
            expected_sales="1000000.000000",
            surprise_ratio="0.120000",
            reason_codes=("existing_home_sales_positive_surprise",),
        ),
    )
    row = digest_report.surprise_rows[0]

    with pytest.raises(ValueError, match="abs_surprise_ratio must match"):
        replace(row, abs_surprise_ratio=d("0.010000"))
    with pytest.raises(ValueError, match="surprise_direction must match"):
        replace(row, surprise_direction="negative")

    inline_row = report(
        observation(
            "source-inline-consistency",
            observed_sales="1000000.000000",
            expected_sales="1000000.000000",
            surprise_ratio="0.000000",
            reason_codes=("existing_home_sales_inline",),
        ),
    ).surprise_rows[0]
    with pytest.raises(ValueError, match="surprise_status must match"):
        replace(inline_row, surprise_status="blocked")
    with pytest.raises(ValueError, match="recommended_next_step must match"):
        replace(
            digest_report,
            recommended_next_step=(
                "allow_report_only_market_research_existing_home_sales_surprise_digest"
            ),
        )
    with pytest.raises(ValueError, match="blocked_observation_ratio must match"):
        replace(digest_report, blocked_observation_ratio=d("0.000000"))
    with pytest.raises(ValueError, match="reason_code_counts must match"):
        replace(digest_report, reason_code_counts=())
    with pytest.raises(ValueError, match="reason code count readonly must be True"):
        replace(digest_report.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        replace(
            digest_report,
            reason_code_counts=tuple(reversed(digest_report.reason_code_counts)),
        )

    two_row_report = report(
        observation(
            "source-z",
            observed_sales="1120000.000000",
            expected_sales="1000000.000000",
            surprise_ratio="0.120000",
            reason_codes=("existing_home_sales_positive_surprise",),
        ),
        observation(
            "source-a",
            observed_sales="1120000.000000",
            expected_sales="1000000.000000",
            surprise_ratio="0.120000",
            reason_codes=("existing_home_sales_positive_surprise",),
        ),
    )
    with pytest.raises(ValueError, match="surprise_rows must be sorted"):
        replace(two_row_report, surprise_rows=tuple(reversed(two_row_report.surprise_rows)))


def test_payload_is_json_ready_and_omits_live_or_durable_surfaces() -> None:
    payload = api().market_research_existing_home_sales_surprise_digest_payload(
        report(
            observation(
                "source-json",
                observed_sales="4210000.000000",
                expected_sales="4100000.000000",
                surprise_ratio="0.026829",
            ),
        ),
    )

    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["source_row_count"] == "2.000000"
    assert payload["observation_count"] == "1.000000"
    assert payload["inline_count"] == "1.000000"
    assert payload["blocked_observation_ratio"] == "0.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["observation_ratio"] == "1.000000"
    assert payload["surprise_rows"][0]["source_row_count"] == "2.000000"
    assert payload["surprise_rows"][0]["observed_sales"] == "4210000.000000"
    assert payload["surprise_rows"][0]["surprise_ratio"] == "0.026829"

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert "wallet" not in key
                assert "order" not in key
                assert "auth" not in key
                assert "database" not in key
                assert "network" not in key
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))
            assert not (type(value) is int)

    walk(payload)
    assert_six_decimal_strings(payload)


def test_public_numeric_count_and_ratio_fields_are_decimal_only() -> None:
    digest = api()
    digest_report = report(observation("source-decimal"))
    row = digest_report.surprise_rows[0]

    for value in (
        digest.ExistingHomeSalesSurpriseDigestConfig(),
        observation("source-dataclass"),
        row,
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        for field in fields(value):
            field_value = getattr(value, field.name)
            if type(field_value) is Decimal:
                assert field_value.as_tuple().exponent == -6, field.name
            elif _is_public_numeric_field(field.name):
                assert type(field_value) is Decimal, field.name


def test_module_has_no_live_durable_or_order_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_existing_home_sales_surprise_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "supabase",
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
        "api_key",
        "secret",
        "private_key",
        "place_order",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "live_trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_calls = {
        "__import__",
        "connect",
        "execute",
        "open",
        "read_text",
        "request",
        "urlopen",
        "write",
        "place_order",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            names = {alias.name.split(".")[0] for alias in node.names}
            assert names.isdisjoint(
                {
                    "requests",
                    "httpx",
                    "aiohttp",
                    "socket",
                    "sqlite3",
                    "urllib",
                    "subprocess",
                    "psycopg",
                    "supabase",
                },
            )
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in {
                "requests",
                "httpx",
                "aiohttp",
                "socket",
                "sqlite3",
                "urllib",
                "subprocess",
                "psycopg",
                "supabase",
            }
        if isinstance(node, ast.Call):
            call_name = call_leaf_name(node.func)
            assert call_name not in forbidden_calls


def assert_six_decimal_strings(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if _is_public_numeric_field(str(key)):
                assert type(child) is str, key
                assert SIX_DECIMAL_RE.fullmatch(child), (key, child)
            assert_six_decimal_strings(child)
    elif isinstance(value, list):
        for child in value:
            assert_six_decimal_strings(child)


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name in {"observed_sales", "expected_sales"}
    )


def call_leaf_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
