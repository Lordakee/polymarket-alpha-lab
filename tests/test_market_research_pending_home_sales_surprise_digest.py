from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_pending_home_sales_surprise_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    region_id: str = "us",
    market_slug: str = "pending-home-sales-above-consensus",
    observed_index: str = "78.600000",
    expected_index: str = "75.000000",
    prior_index: str = "74.500000",
    surprise_ratio: str = "0.048000",
    source_row_count: str = "2",
    data_timestamp: datetime = datetime(2026, 7, 3, 11, 30, tzinfo=UTC),
    reason_codes: tuple[str, ...] = ("pending_home_sales_inline",),
):
    module = digest()
    return module.PendingHomeSalesSurpriseObservation(
        source_id=source_id,
        region_id=region_id,
        market_slug=market_slug,
        observed_index=observed_index if isinstance(observed_index, Decimal) else d(observed_index),
        expected_index=expected_index if isinstance(expected_index, Decimal) else d(expected_index),
        prior_index=prior_index if isinstance(prior_index, Decimal) else d(prior_index),
        surprise_ratio=surprise_ratio if isinstance(surprise_ratio, Decimal) else d(surprise_ratio),
        source_row_count=(
            source_row_count
            if isinstance(source_row_count, Decimal)
            else d(source_row_count)
        ),
        data_timestamp=data_timestamp,
        reason_codes=reason_codes,
    )


def report(*rows):
    module = digest()
    return module.build_market_research_pending_home_sales_surprise_digest(
        rows,
        config=module.PendingHomeSalesSurpriseDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_pending_home_sales_digest_reduces_surprises_deterministically() -> None:
    module = digest()

    digest_report = report(
        observation(
            "source-inline",
            region_id="midwest",
            market_slug="midwest-pending-home-sales-inline",
            observed_index="99.000000",
            expected_index="100.000000",
            prior_index="100.500000",
            surprise_ratio="-0.010000",
            source_row_count="1",
            data_timestamp=datetime(
                2026,
                7,
                3,
                8,
                15,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            reason_codes=("pending_home_sales_inline",),
        ),
        observation(
            "source-watch",
            region_id="south",
            market_slug="south-pending-home-sales-miss",
            observed_index="94.000000",
            expected_index="100.000000",
            prior_index="99.000000",
            surprise_ratio="-0.060000",
            source_row_count="2",
            reason_codes=("pending_home_sales_negative_surprise",),
        ),
        observation(
            "source-blocked",
            region_id="west",
            market_slug="west-pending-home-sales-spike",
            observed_index="112.000000",
            expected_index="100.000000",
            prior_index="101.000000",
            surprise_ratio="0.120000",
            source_row_count="3",
            data_timestamp=datetime(2026, 7, 3, 12, 45, tzinfo=UTC),
            reason_codes=("pending_home_sales_positive_surprise",),
        ),
    )

    assert isinstance(digest_report, module.PendingHomeSalesSurpriseDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-pending-home-sales-surprise-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_pending_home_sales_surprise_digest"
    )
    assert digest_report.source_row_count == d("6")
    assert digest_report.observation_count == d("3")
    assert digest_report.positive_surprise_count == d("1")
    assert digest_report.negative_surprise_count == d("1")
    assert digest_report.inline_count == d("1")
    assert digest_report.max_abs_surprise_ratio == d("0.120000")
    assert digest_report.average_surprise_ratio == d("0.016667")
    assert digest_report.blocked_observation_ratio == d("0.333333")
    assert digest_report.reason_codes == (
        "pending_home_sales_large_surprise_present",
        "pending_home_sales_mixed_surprises_present",
    )
    assert digest_report.reason_code_counts == (
        module.PendingHomeSalesSurpriseReasonCodeCount(
            reason_code="pending_home_sales_large_surprise_present",
            count=d("1"),
            observation_ratio=d("0.333333"),
        ),
        module.PendingHomeSalesSurpriseReasonCodeCount(
            reason_code="pending_home_sales_mixed_surprises_present",
            count=d("1"),
            observation_ratio=d("0.333333"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.market_slug for row in digest_report.surprise_rows) == (
        "west-pending-home-sales-spike",
        "south-pending-home-sales-miss",
        "midwest-pending-home-sales-inline",
    )
    blocked, watch, passed = digest_report.surprise_rows
    assert blocked.region_id == "west"
    assert blocked.surprise_direction == "positive"
    assert blocked.surprise_status == "blocked"
    assert blocked.abs_surprise_ratio == d("0.120000")
    assert blocked.data_timestamp == datetime(2026, 7, 3, 12, 45, tzinfo=UTC)
    assert blocked.reason_codes == (
        "pending_home_sales_segment_large_positive_surprise",
    )
    assert watch.surprise_direction == "negative"
    assert watch.surprise_status == "watch"
    assert watch.reason_codes == (
        "pending_home_sales_segment_negative_surprise",
    )
    assert passed.surprise_direction == "inline"
    assert passed.surprise_status == "pass"
    assert passed.data_timestamp == datetime(2026, 7, 3, 12, 15, tzinfo=UTC)
    assert passed.reason_codes == ("pending_home_sales_segment_inline",)


def test_empty_digest_is_report_only_blocked_and_decimal_zeroed() -> None:
    module = digest()

    digest_report = report()

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_pending_home_sales_surprise_digest"
    )
    assert digest_report.source_row_count == d("0")
    assert digest_report.observation_count == d("0")
    assert digest_report.positive_surprise_count == d("0")
    assert digest_report.negative_surprise_count == d("0")
    assert digest_report.inline_count == d("0")
    assert digest_report.max_abs_surprise_ratio == d("0.000000")
    assert digest_report.average_surprise_ratio == d("0.000000")
    assert digest_report.blocked_observation_ratio == d("0.000000")
    assert digest_report.surprise_rows == ()
    assert digest_report.reason_codes == (
        "pending_home_sales_surprise_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.PendingHomeSalesSurpriseReasonCodeCount(
            reason_code="pending_home_sales_surprise_digest_empty",
            count=d("1"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_validates_decimal_datetime_flags_duplicates_and_consistency() -> None:
    module = digest()

    with pytest.raises(ValueError, match="observed_index must be a Decimal"):
        observation(observed_index=_DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="expected_index must be positive"):
        observation(expected_index="0.000000")
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_pending_home_sales_surprise_digest(
            (),
            config=module.PendingHomeSalesSurpriseDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_research_pending_home_sales_surprise_digest(
            (),
            config=module.PendingHomeSalesSurpriseDigestConfig(),
            generated_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="reason_codes must match surprise direction"):
        observation(
            observed_index="112.000000",
            expected_index="100.000000",
            surprise_ratio="0.120000",
            reason_codes=("pending_home_sales_negative_surprise",),
        )
    with pytest.raises(ValueError, match="surprise_ratio must match observed and expected"):
        observation(
            observed_index="112.000000",
            expected_index="100.000000",
            surprise_ratio="0.010000",
        )
    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(observation("source-dupe"), observation("source-dupe"))
    sample_report = report(observation("source-flags"))
    for value in (
        module.PendingHomeSalesSurpriseDigestConfig(),
        observation("source-flag-observation"),
        sample_report.surprise_rows[0],
        sample_report.reason_code_counts[0],
        sample_report,
    ):
        for flag_name in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match=f"{flag_name} must be True"):
                replace(value, **{flag_name: False})

    row = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.observed_index = d("200.000000")  # type: ignore[misc]


def test_payload_public_numeric_fields_and_no_live_or_durable_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-json"))

    payload = module.market_research_pending_home_sales_surprise_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_row_count"] == "2.000000"
    assert payload["observation_count"] == "1.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["surprise_rows"][0]["observed_index"] == "78.600000"
    assert payload["surprise_rows"][0]["surprise_ratio"] == "0.048000"

    for value in (
        module.PendingHomeSalesSurpriseDigestConfig(),
        observation("source-decimal"),
        digest_report.surprise_rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if _is_public_numeric_count_or_ratio(field.name):
                field_value = getattr(value, field.name)
                assert type(field_value) is Decimal, field.name

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                assert "database" not in lowered
                assert "network" not in lowered
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk(payload)

    source = Path(
        "src/polymarket_alpha_lab/market_research_pending_home_sales_surprise_digest.py",
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
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    forbidden_call_names = (
        "connect",
        "open",
        "read_bytes",
        "read_text",
        "request",
        "urlopen",
        "write_bytes",
        "write_text",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            else:
                continue
            assert call_name not in forbidden_call_names
    for forbidden in (
        "account",
        "api_key",
        "auth",
        "broker",
        "cancel_order",
        "database",
        "exchange",
        "live trading",
        "network",
        "private_key",
        "replace_order",
        "secret",
        "signing",
        "submit_order",
        "wallet",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric_count_or_ratio(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_index")
    )
