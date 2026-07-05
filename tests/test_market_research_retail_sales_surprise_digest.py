from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 14, 30, tzinfo=timezone(timedelta(hours=-4)))


class NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


class DatetimeSubclass(datetime):
    pass


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_retail_sales_surprise_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def observation(
    source_id: str,
    *,
    region_id: str = "us",
    segment_id: str = "headline",
    observed_sales: str = "101.0",
    expected_sales: str = "100.0",
    surprise_ratio: str = "0.010000",
    source_row_count: str = "1",
    data_timestamp: datetime = datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
    reason_codes: tuple[str, ...] = ("retail_sales_positive_surprise",),
):
    digest = api()
    return digest.RetailSalesSurpriseObservation(
        source_id=source_id,
        region_id=region_id,
        segment_id=segment_id,
        observed_sales=d(observed_sales),
        expected_sales=d(expected_sales),
        surprise_ratio=d(surprise_ratio),
        source_row_count=d(source_row_count),
        data_timestamp=data_timestamp,
        reason_codes=reason_codes,
    )


def report(*rows):
    digest = api()
    return digest.build_market_research_retail_sales_surprise_digest(
        rows,
        config=digest.RetailSalesSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )


def test_digest_reduces_retail_sales_surprises_with_deterministic_rows() -> None:
    digest_report = report(
        observation(
            "source-watch",
            segment_id="control",
            observed_sales="100.0",
            expected_sales="100.0",
            surprise_ratio="0.000000",
            source_row_count="2",
            data_timestamp=datetime(2026, 7, 3, 8, 15, tzinfo=timezone(timedelta(hours=-4))),
            reason_codes=("retail_sales_inline",),
        ),
        observation(
            "source-blocked",
            segment_id="electronics",
            observed_sales="107.5",
            expected_sales="100.0",
            surprise_ratio="0.075000",
            source_row_count="3",
            data_timestamp=datetime(2026, 7, 3, 12, 45, tzinfo=UTC),
            reason_codes=("retail_sales_positive_surprise",),
        ),
        observation(
            "source-negative",
            segment_id="grocery",
            observed_sales="96.0",
            expected_sales="100.0",
            surprise_ratio="-0.040000",
            source_row_count="1",
            data_timestamp=datetime(2026, 7, 3, 11, 30, tzinfo=UTC),
            reason_codes=("retail_sales_negative_surprise",),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == datetime(2026, 7, 3, 18, 30, tzinfo=UTC)
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == "market-research-retail-sales-surprise-digest-v0"
    assert digest_report.source_row_count == d("6")
    assert digest_report.observation_count == d("3")
    assert digest_report.positive_surprise_count == d("1")
    assert digest_report.negative_surprise_count == d("1")
    assert digest_report.inline_count == d("1")
    assert digest_report.max_abs_surprise_ratio == d("0.075000")
    assert digest_report.average_surprise_ratio == d("0.011667")
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_retail_sales_surprise_screening"
    )
    assert digest_report.reason_codes == (
        "retail_sales_large_surprise_present",
        "retail_sales_mixed_surprises_present",
    )
    assert digest_report.reason_code_counts == (
        api().RetailSalesSurpriseReasonCodeCount(
            reason_code="retail_sales_large_surprise_present",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        api().RetailSalesSurpriseReasonCodeCount(
            reason_code="retail_sales_mixed_surprises_present",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.segment_id for row in digest_report.surprise_rows) == (
        "electronics",
        "grocery",
        "control",
    )
    assert digest_report.surprise_rows[0].surprise_direction == "positive"
    assert digest_report.surprise_rows[0].surprise_status == "blocked"
    assert digest_report.surprise_rows[0].reason_codes == (
        "retail_sales_segment_large_positive_surprise",
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
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_retail_sales_surprise_screening"
    )
    assert digest_report.reason_codes == ("retail_sales_surprise_digest_no_inputs",)
    assert digest_report.reason_code_counts == (
        api().RetailSalesSurpriseReasonCodeCount(
            reason_code="retail_sales_surprise_digest_no_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.surprise_rows == ()


def test_digest_rejects_float_inputs_false_flags_duplicates_and_mutation() -> None:
    digest = api()

    with pytest.raises(ValueError, match="observed_sales must be a Decimal"):
        digest.RetailSalesSurpriseObservation(
            source_id="source-float",
            region_id="us",
            segment_id="headline",
            observed_sales=101.0,
            expected_sales=d("100.0"),
            surprise_ratio=d("0.010000"),
            source_row_count=d("1"),
            data_timestamp=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
            reason_codes=("retail_sales_positive_surprise",),
        )

    with pytest.raises(ValueError, match="observed_sales must be a Decimal"):
        digest.RetailSalesSurpriseObservation(
            source_id="source-decimal-subclass",
            region_id="us",
            segment_id="headline",
            observed_sales=DecimalSubclass("101.0"),
            expected_sales=d("100.0"),
            surprise_ratio=d("0.010000"),
            source_row_count=d("1"),
            data_timestamp=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
            reason_codes=("retail_sales_positive_surprise",),
        )

    row = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.observed_sales = d("200")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        digest.RetailSalesSurpriseDigestConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        digest.RetailSalesSurpriseDigestConfig(report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        digest.RetailSalesSurpriseDigestConfig(readonly=False)

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(observation("source-dupe"), observation("source-dupe"))


def test_public_dataclasses_reject_subclasses_and_bad_config_versions() -> None:
    digest = api()
    digest_report = report(observation("source-exact-type"))

    class ConfigSubclass(digest.RetailSalesSurpriseDigestConfig):
        pass

    class ObservationSubclass(digest.RetailSalesSurpriseObservation):
        pass

    class RowSubclass(digest.RetailSalesSurpriseDigestRow):
        pass

    class ReasonCodeCountSubclass(digest.RetailSalesSurpriseReasonCodeCount):
        pass

    class ReportSubclass(digest.RetailSalesSurpriseDigestReport):
        pass

    with pytest.raises(
        ValueError,
        match="config must be exactly RetailSalesSurpriseDigestConfig",
    ):
        ConfigSubclass()

    with pytest.raises(
        ValueError,
        match="observation must be exactly RetailSalesSurpriseObservation",
    ):
        ObservationSubclass(
            source_id="source-observation-subclass",
            region_id="us",
            segment_id="headline",
            observed_sales=d("101.0"),
            expected_sales=d("100.0"),
            surprise_ratio=d("0.010000"),
            source_row_count=d("1"),
            data_timestamp=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
            reason_codes=("retail_sales_positive_surprise",),
        )

    row_kwargs = {
        field.name: getattr(digest_report.surprise_rows[0], field.name)
        for field in fields(digest_report.surprise_rows[0])
    }
    with pytest.raises(
        ValueError,
        match="row must be exactly RetailSalesSurpriseDigestRow",
    ):
        RowSubclass(**row_kwargs)

    reason_count_kwargs = {
        field.name: getattr(digest_report.reason_code_counts[0], field.name)
        for field in fields(digest_report.reason_code_counts[0])
    }
    with pytest.raises(
        ValueError,
        match="reason code count must be exactly RetailSalesSurpriseReasonCodeCount",
    ):
        ReasonCodeCountSubclass(**reason_count_kwargs)

    report_kwargs = {
        field.name: getattr(digest_report, field.name)
        for field in fields(digest_report)
    }
    with pytest.raises(
        ValueError,
        match="report must be exactly RetailSalesSurpriseDigestReport",
    ):
        ReportSubclass(**report_kwargs)

    with pytest.raises(
        ValueError,
        match="config_version must be the supported config version",
    ):
        digest.RetailSalesSurpriseDigestConfig(
            config_version="market-research-retail-sales-surprise-digest-v1",
        )

    with pytest.raises(
        ValueError,
        match="config_version must be the supported config version",
    ):
        replace(
            digest_report,
            config_version="market-research-retail-sales-surprise-digest-v1",
        )


def test_digest_validates_timestamp_reason_codes_and_surprise_math() -> None:
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(
            "source-naive",
            data_timestamp=datetime(2026, 7, 3, 12, 0),
        )

    with pytest.raises(ValueError, match="data_timestamp must have a UTC offset"):
        observation(
            "source-none-offset",
            data_timestamp=datetime(2026, 7, 3, 12, 0, tzinfo=NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="data_timestamp must be a datetime"):
        observation(
            "source-datetime-subclass",
            data_timestamp=DatetimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="reason_codes must match surprise direction"):
        observation(
            "source-bad-reason",
            observed_sales="107.0",
            expected_sales="100.0",
            surprise_ratio="0.070000",
            reason_codes=("retail_sales_negative_surprise",),
        )

    with pytest.raises(ValueError, match="surprise_ratio must match observed and expected"):
        observation(
            "source-bad-math",
            observed_sales="110.0",
            expected_sales="100.0",
            surprise_ratio="0.070000",
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        observation("source-token")


def test_digest_rejects_public_integer_numerics() -> None:
    digest = api()

    with pytest.raises(ValueError, match="source_row_count must be a Decimal"):
        digest.RetailSalesSurpriseObservation(
            source_id="source-int-count",
            region_id="us",
            segment_id="headline",
            observed_sales=d("101.0"),
            expected_sales=d("100.0"),
            surprise_ratio=d("0.010000"),
            source_row_count=1,
            data_timestamp=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
            reason_codes=("retail_sales_positive_surprise",),
        )

    with pytest.raises(ValueError, match="watch_abs_surprise_ratio must be a Decimal"):
        digest.RetailSalesSurpriseDigestConfig(watch_abs_surprise_ratio=2)


def test_payload_is_json_ready_and_omits_live_or_durable_surfaces() -> None:
    payload = api().market_research_retail_sales_surprise_digest_payload(
        report(
            observation(
                "source-json",
                observed_sales="107.5",
                expected_sales="100.0",
                surprise_ratio="0.075000",
            ),
        ),
    )

    json.dumps(payload, sort_keys=True)
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))
    assert not any(isinstance(value, float) for value in walk_values(payload))
    payload_text = repr(payload).lower()
    for forbidden in (
        "market_slug",
        "question",
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "durable",
    ):
        assert forbidden not in payload_text
    assert payload["source_row_count"] == "1.000000"
    assert payload["observation_count"] == "1.000000"
    assert payload["positive_surprise_count"] == "1.000000"
    assert (
        payload["recommended_next_step"]
        == "block_report_only_retail_sales_surprise_screening"
    )
    assert payload["surprise_rows"][0]["surprise_ratio"] == "0.075000"
    assert payload["surprise_rows"][0]["source_row_count"] == "1.000000"
    assert payload["surprise_rows"][0]["data_timestamp"] == "2026-07-03T12:00:00+00:00"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "1.000000"


def test_payload_rejects_raw_dict_inputs_even_when_json_ready() -> None:
    digest = api()
    payload = digest.market_research_retail_sales_surprise_digest_payload(
        report(observation("source-dict")),
    )

    with pytest.raises(
        ValueError,
        match="report must be exactly RetailSalesSurpriseDigestReport",
    ):
        digest.market_research_retail_sales_surprise_digest_payload(
            payload,
        )

    with pytest.raises(
        ValueError,
        match="report must be exactly RetailSalesSurpriseDigestReport",
    ):
        digest.market_research_retail_sales_surprise_digest_payload(
            {**payload, "paper_only": False},
        )

    with pytest.raises(
        ValueError,
        match="report must be exactly RetailSalesSurpriseDigestReport",
    ):
        digest.market_research_retail_sales_surprise_digest_payload(
            {
                **payload,
                "surprise_rows": [{**payload["surprise_rows"][0], "paper_only": False}],
            },
        )


def test_payload_rejects_tampered_report_and_row_flags() -> None:
    digest = api()
    digest_report = report(observation("source-tamper"))

    object.__setattr__(digest_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        digest.market_research_retail_sales_surprise_digest_payload(digest_report)

    digest_report = report(observation("source-row-tamper"))
    object.__setattr__(digest_report.surprise_rows[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        digest.market_research_retail_sales_surprise_digest_payload(digest_report)


def test_report_rejects_inconsistent_next_step_counts_and_reason_count_flags() -> None:
    digest = api()
    digest_report = report(
        observation(
            "source-report-consistency",
            observed_sales="107.5",
            expected_sales="100.0",
            surprise_ratio="0.075000",
        ),
    )

    with pytest.raises(ValueError, match="recommended_next_step must match digest_status"):
        replace(
            digest_report,
            recommended_next_step="allow_report_only_retail_sales_surprise_screening",
        )

    with pytest.raises(ValueError, match="reason_code_counts must match reason_codes"):
        replace(digest_report, reason_code_counts=())
    with pytest.raises(ValueError, match="reason_code_counts must be deterministic"):
        replace(
            digest_report,
            reason_code_counts=tuple(reversed(digest_report.reason_code_counts)),
        )

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(digest_report.reason_code_counts[0], report_only=False)


def test_module_scope_has_no_network_file_db_fast_or_live_trading_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_retail_sales_surprise_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "urlopen",
        "connect(",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "shelve",
        "pickle",
        "open(",
        "pathlib",
        "auth",
        "wallet",
        "account",
        "private_key",
        "api_key",
        "market_slug",
        "question",
        "order",
        "cancel",
        "replace",
        "exchange_mutation",
        "trade",
        "durable",
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "connect",
                "float",
                "open",
                "request",
                "urlopen",
            }
