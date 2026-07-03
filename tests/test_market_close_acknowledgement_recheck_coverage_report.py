from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_close_acknowledgement_recheck_coverage_report",
    )


def base_api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_close_acknowledgement_recheck_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def base_cfg():
    module = base_api()
    return module.MarketCloseAcknowledgementRecheckConfig(
        stale_acknowledgement_seconds=d("3600.000000"),
        close_age_pressure_seconds=d("10800.000000"),
    )


def cfg(**overrides: object):
    module = api()
    values = {
        "close_time_bucket_bounds_seconds": (
            d("3600.000000"),
            d("7200.000000"),
            d("14400.000000"),
        ),
        "min_ack_coverage_ratio": d("0.750000"),
        "max_missing_ack_ratio": d("0.000000"),
        "max_stale_recheck_ratio": d("0.250000"),
    }
    values.update(overrides)
    return module.MarketCloseAcknowledgementRecheckCoverageConfig(**values)


def input_row(
    market_id: str,
    *,
    team_owner_id: str | None = "resolution-team",
    source_id: str = "official-source",
    latest_update_id: str = "update-current",
    acknowledged_update_id: str | None = "update-current",
    market_closed_at: datetime = GENERATED_AT - timedelta(minutes=45),
    latest_update_at: datetime = GENERATED_AT - timedelta(minutes=30),
    acknowledgement_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
    source_contradicts_outcome: bool = False,
):
    module = base_api()
    return module.MarketCloseAcknowledgementRecheckInputRow(
        market_id=market_id,
        team_owner_id=team_owner_id,
        source_id=source_id,
        latest_update_id=latest_update_id,
        acknowledged_update_id=acknowledged_update_id,
        market_closed_at=market_closed_at,
        latest_update_at=latest_update_at,
        acknowledgement_at=acknowledgement_at,
        source_contradicts_outcome=source_contradicts_outcome,
    )


def source_rows(*rows: object):
    module = base_api()
    return module.build_market_close_acknowledgement_recheck_report(
        rows,
        config=base_cfg(),
        generated_at=GENERATED_AT,
    ).rows


def coverage_report(*rows: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_close_acknowledgement_recheck_coverage_report(
        rows,
        config=cfg(),
        generated_at=generated_at,
    )


def mixed_source_rows():
    return source_rows(
        input_row(
            "m-ready-recent",
            market_closed_at=GENERATED_AT - timedelta(minutes=45),
            latest_update_at=GENERATED_AT - timedelta(minutes=30),
            acknowledgement_at=GENERATED_AT - timedelta(minutes=20),
        ),
        input_row(
            "m-stale-mid",
            market_closed_at=GENERATED_AT - timedelta(seconds=9000),
            latest_update_at=GENERATED_AT - timedelta(hours=2),
            acknowledgement_at=GENERATED_AT - timedelta(minutes=70),
        ),
        input_row(
            "m-missing-long",
            market_closed_at=GENERATED_AT - timedelta(hours=5),
            latest_update_at=GENERATED_AT - timedelta(hours=4),
            acknowledgement_at=None,
            acknowledged_update_id=None,
        ),
        input_row(
            "m-stale-long",
            market_closed_at=GENERATED_AT - timedelta(hours=6),
            latest_update_at=GENERATED_AT - timedelta(hours=5),
            acknowledgement_at=GENERATED_AT - timedelta(hours=4),
            acknowledged_update_id="update-previous",
        ),
    )


def test_empty_coverage_report_is_ready_with_decimal_zeroes() -> None:
    report = coverage_report()

    assert report.report_status == "ready"
    assert report.reason_codes == (
        "market_close_acknowledgement_recheck_coverage_clear",
    )
    assert report.source_row_count == d("0.000000")
    assert report.close_time_bucket_count == d("4.000000")
    assert report.covered_close_time_bucket_count == d("0.000000")
    assert report.close_time_bucket_coverage_ratio == d("0.000000")
    assert report.ack_covered_count == d("0.000000")
    assert report.ack_coverage_ratio == d("0.000000")
    assert report.missing_ack_count == d("0.000000")
    assert report.missing_ack_ratio == d("0.000000")
    assert report.stale_recheck_count == d("0.000000")
    assert report.stale_recheck_ratio == d("0.000000")
    assert report.max_market_close_age_seconds == d("0.000000")
    assert report.max_acknowledgement_age_seconds == d("0.000000")
    assert report.close_time_bucket_rows == ()
    assert report.ack_coverage_rows == ()
    assert report.missing_ack_coverage_rows == ()
    assert report.stale_recheck_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_coverage_report_groups_ack_missing_stale_and_close_time_buckets() -> None:
    report = coverage_report(*mixed_source_rows())

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api().DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_COVERAGE_CONFIG_VERSION
    )
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "close_time_bucket_coverage_gap",
        "acknowledgement_coverage_gap",
        "missing_acknowledgement_coverage_gap",
        "stale_recheck_coverage_gap",
    )
    assert report.source_row_count == d("4.000000")
    assert report.close_time_bucket_count == d("4.000000")
    assert report.covered_close_time_bucket_count == d("3.000000")
    assert report.close_time_bucket_coverage_ratio == d("0.750000")
    assert report.ack_covered_count == d("2.000000")
    assert report.ack_coverage_ratio == d("0.500000")
    assert report.missing_ack_count == d("1.000000")
    assert report.missing_ack_ratio == d("0.250000")
    assert report.stale_recheck_count == d("3.000000")
    assert report.stale_recheck_ratio == d("0.750000")
    assert report.max_market_close_age_seconds == d("21600.000000")
    assert report.max_acknowledgement_age_seconds == d("14400.000000")

    assert tuple(row.close_time_bucket_label for row in report.close_time_bucket_rows) == (
        "0_to_3600_seconds",
        "7200_to_14400_seconds",
        "14400_plus_seconds",
    )
    assert tuple(row.bucket_status for row in report.close_time_bucket_rows) == (
        "ready",
        "watch",
        "blocked",
    )
    assert tuple(row.source_row_count for row in report.close_time_bucket_rows) == (
        d("1.000000"),
        d("1.000000"),
        d("2.000000"),
    )
    assert tuple(row.ack_covered_count for row in report.close_time_bucket_rows) == (
        d("1.000000"),
        d("1.000000"),
        d("0.000000"),
    )
    assert tuple(row.missing_ack_count for row in report.close_time_bucket_rows) == (
        d("0.000000"),
        d("0.000000"),
        d("1.000000"),
    )

    assert tuple(row.ack_coverage_status for row in report.ack_coverage_rows) == (
        "not_covered",
        "covered",
    )
    assert tuple(row.source_row_count for row in report.ack_coverage_rows) == (
        d("2.000000"),
        d("2.000000"),
    )
    assert tuple(row.coverage_ratio for row in report.ack_coverage_rows) == (
        d("0.500000"),
        d("0.500000"),
    )

    assert tuple(
        row.missing_ack_status for row in report.missing_ack_coverage_rows
    ) == ("missing", "present")
    assert tuple(
        row.source_row_count for row in report.missing_ack_coverage_rows
    ) == (d("1.000000"), d("3.000000"))

    assert tuple(row.stale_recheck_status for row in report.stale_recheck_rows) == (
        "stale",
        "fresh",
    )
    assert tuple(row.source_row_count for row in report.stale_recheck_rows) == (
        d("3.000000"),
        d("1.000000"),
    )


def test_coverage_report_warns_on_close_time_bucket_gap_only() -> None:
    report = coverage_report(
        *source_rows(
            input_row(
                "m-ready-recent",
                market_closed_at=GENERATED_AT - timedelta(minutes=45),
                latest_update_at=GENERATED_AT - timedelta(minutes=30),
                acknowledgement_at=GENERATED_AT - timedelta(minutes=20),
            ),
        ),
    )

    assert report.report_status == "watch"
    assert report.reason_codes == ("close_time_bucket_coverage_gap",)
    assert report.source_row_count == d("1.000000")
    assert report.covered_close_time_bucket_count == d("1.000000")
    assert report.close_time_bucket_coverage_ratio == d("0.250000")
    assert report.ack_coverage_ratio == d("1.000000")
    assert report.missing_ack_ratio == d("0.000000")
    assert report.stale_recheck_ratio == d("0.000000")


def test_coverage_report_sorting_is_deterministic() -> None:
    report = coverage_report(*tuple(reversed(mixed_source_rows())))

    assert tuple(row.close_time_bucket_label for row in report.close_time_bucket_rows) == (
        "0_to_3600_seconds",
        "7200_to_14400_seconds",
        "14400_plus_seconds",
    )
    assert tuple(row.ack_coverage_status for row in report.ack_coverage_rows) == (
        "not_covered",
        "covered",
    )
    assert tuple(
        row.missing_ack_status for row in report.missing_ack_coverage_rows
    ) == ("missing", "present")
    assert tuple(row.stale_recheck_status for row in report.stale_recheck_rows) == (
        "stale",
        "fresh",
    )


def test_coverage_report_accepts_multi_source_same_market_update() -> None:
    first = source_rows(
        input_row(
            "m-shared-update",
            source_id="official-source-a",
            latest_update_id="update-shared",
            acknowledged_update_id="update-shared",
        ),
    )[0]
    second = replace(first, source_id="official-source-b")

    report = coverage_report(second, first)

    assert report.source_row_count == d("2.000000")
    assert report.ack_covered_count == d("2.000000")
    assert tuple(row.source_row_count for row in report.close_time_bucket_rows) == (
        d("2.000000"),
    )


def test_coverage_report_rejects_duplicate_market_update_source_key() -> None:
    first = source_rows(
        input_row(
            "m-duplicate-key",
            source_id="official-source-a",
            latest_update_id="update-shared",
            acknowledged_update_id="update-shared",
        ),
    )[0]

    with pytest.raises(ValueError, match="unique"):
        coverage_report(first, replace(first))


def test_coverage_report_rejects_naive_generated_at_and_normalizes_offsets() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at"):
        module.build_market_close_acknowledgement_recheck_coverage_report(
            (),
            config=cfg(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )

    eastern = timezone(timedelta(hours=-4))
    report = module.build_market_close_acknowledgement_recheck_coverage_report(
        (),
        config=cfg(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=eastern),
    )
    assert report.generated_at == GENERATED_AT


def test_coverage_dataclasses_are_frozen_and_decimal_public_metrics() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_COVERAGE_CONFIG_VERSION",
        "MarketCloseAcknowledgementRecheckAckCoverageRow",
        "MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow",
        "MarketCloseAcknowledgementRecheckCoverageConfig",
        "MarketCloseAcknowledgementRecheckCoverageReport",
        "MarketCloseAcknowledgementRecheckMissingAckCoverageRow",
        "MarketCloseAcknowledgementRecheckStaleCoverageRow",
        "build_market_close_acknowledgement_recheck_coverage_report",
        "market_close_acknowledgement_recheck_coverage_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True
            defaults = {field.name: field.default for field in fields(value)}
            assert defaults["paper_only"] is True
            assert defaults["report_only"] is True
            assert defaults["readonly"] is True
            for field_name, hint in get_type_hints(value).items():
                if field_name in {"paper_only", "report_only", "readonly"}:
                    continue
                assert not _type_uses_float(hint)

    report = coverage_report(*mixed_source_rows())

    with pytest.raises(FrozenInstanceError):
        report.report_status = "ready"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.close_time_bucket_rows[0].bucket_status = "blocked"  # type: ignore[misc]

    for value in report.config_close_time_bucket_bounds_seconds:
        assert type(value) is Decimal
    for value in (
        report,
        *report.close_time_bucket_rows,
        *report.ack_coverage_rows,
        *report.missing_ack_coverage_rows,
        *report.stale_recheck_rows,
    ):
        _assert_decimal_public_metrics(value)

    with pytest.raises(ValueError, match="close_time_bucket_bounds_seconds"):
        module.MarketCloseAcknowledgementRecheckCoverageConfig(
            close_time_bucket_bounds_seconds=(d("3600.000000"), d("3600.000000")),
        )
    with pytest.raises(ValueError, match="integral seconds"):
        module.MarketCloseAcknowledgementRecheckCoverageConfig(
            close_time_bucket_bounds_seconds=(d("3600.500000"),),
        )
    with pytest.raises(ValueError, match="min_ack_coverage_ratio"):
        module.MarketCloseAcknowledgementRecheckCoverageConfig(
            min_ack_coverage_ratio=_DecimalSubclass("0.750000"),
        )
    with pytest.raises(ValueError, match="max_missing_ack_ratio"):
        module.MarketCloseAcknowledgementRecheckCoverageConfig(
            max_missing_ack_ratio=d("1.000001"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.MarketCloseAcknowledgementRecheckCoverageConfig(), paper_only=False)
    with pytest.raises(ValueError, match="source_rows"):
        module.build_market_close_acknowledgement_recheck_coverage_report(
            (object(),),
            config=cfg(),
            generated_at=GENERATED_AT,
        )


def test_coverage_payload_is_json_ready_with_decimal_strings_and_no_floats() -> None:
    payload = api().market_close_acknowledgement_recheck_coverage_report_payload(
        coverage_report(*mixed_source_rows()),
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)

    assert_no_float_values(payload)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["source_row_count"] == "4.000000"
    assert payload["ack_coverage_ratio"] == "0.500000"
    assert payload["missing_ack_ratio"] == "0.250000"
    assert payload["stale_recheck_ratio"] == "0.750000"
    assert payload["close_time_bucket_rows"][0]["source_row_count"] == "1.000000"
    assert payload["ack_coverage_rows"][0]["coverage_ratio"] == "0.500000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(ValueError, match="report"):
        api().market_close_acknowledgement_recheck_coverage_report_payload(object())


def test_coverage_module_scope_is_report_only_and_in_memory() -> None:
    source_path = Path(
        "src/polymarket_alpha_lab/market_close_acknowledgement_recheck_coverage_report.py",
    )
    source = source_path.read_text(encoding="utf-8")
    lowered = source.lower()

    for blocked_text in (
        _join("data", "base"),
        _join("net", "work"),
        _join("li", "ve"),
        _join("tra", "ding"),
        _join("au", "th"),
        _join("wal", "let"),
        _join("bro", "ker"),
        _join("or", "der"),
        _join("sig", "ning"),
        _join("ad", "vice"),
        "open(",
        "path(",
        "json.",
        "request",
        "http",
        "socket",
        "psycopg",
        "sqlite",
    ):
        assert blocked_text not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
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
                "float",
            }


def _assert_decimal_public_metrics(value: object) -> None:
    for field in fields(value):
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
        ):
            item = getattr(value, field.name)
            if isinstance(item, tuple):
                assert item
                assert all(type(member) is Decimal for member in item)
            else:
                assert type(item) is Decimal


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float value found: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_no_float_values(item)


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))


def _join(*parts: str) -> str:
    return "".join(parts)
