from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
import inspect

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
WINDOW_START = datetime(2026, 7, 5, 0, 0, tzinfo=UTC)
WINDOW_END = datetime(2026, 7, 6, 0, 0, tzinfo=UTC)


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


def _api():
    return import_module("polymarket_alpha_lab.market_event_cluster_exposure_report")


def _config(**overrides):
    values = {
        "config_version": "market-event-cluster-exposure-report-test-v1",
        "watch_exposure_share_threshold": d("0.400000"),
        "concentrated_exposure_share_threshold": d("0.600000"),
        "watch_unresolved_share_threshold": d("0.400000"),
        "concentrated_unresolved_share_threshold": d("0.600000"),
    }
    values.update(overrides)
    return _api().MarketEventClusterExposureReportConfig(**values)


def _source_row(
    *,
    cluster_id: str,
    team: str,
    category: str,
    paper_exposure: Decimal,
    unresolved_count: Decimal,
    window_start: datetime = WINDOW_START,
    window_end: datetime = WINDOW_END,
):
    return _api().MarketEventClusterExposureSourceRow(
        cluster_id=cluster_id,
        team=team,
        category=category,
        paper_exposure=paper_exposure,
        unresolved_count=unresolved_count,
        expected_resolution_window_start_at=window_start,
        expected_resolution_window_end_at=window_end,
    )


def _report(*rows, **config_overrides):
    return _api().build_market_event_cluster_exposure_report(
        rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_cluster_exposure_report_reduces_rows_and_sorts_deterministically() -> None:
    api = _api()
    rows = (
        _source_row(
            cluster_id="cluster_beta",
            team="sports_team",
            category="soccer",
            paper_exposure=d("40.0000"),
            unresolved_count=d("1"),
            window_start=datetime(2026, 7, 6, 0, 0, tzinfo=UTC),
            window_end=datetime(2026, 7, 7, 0, 0, tzinfo=UTC),
        ),
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("60.0000"),
            unresolved_count=d("3"),
            window_start=WINDOW_START,
            window_end=WINDOW_END,
        ),
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("20.0000"),
            unresolved_count=d("1"),
            window_start=WINDOW_START - timedelta(days=1),
            window_end=WINDOW_END + timedelta(days=1),
        ),
    )

    report = _report(*rows)

    assert type(report) is api.MarketEventClusterExposureReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-event-cluster-exposure-report-test-v1"
    assert report.source_row_count == d("3")
    assert report.cluster_count == d("2")
    assert report.total_paper_exposure == d("120.0000")
    assert report.total_unresolved_count == d("5")
    assert report.top_cluster_id == "cluster_alpha"
    assert report.top_cluster_exposure_share == d("0.666667")
    assert report.top_cluster_unresolved_share == d("0.800000")
    assert report.concentration_status == "concentrated"
    assert report.reason_codes == (
        "cluster_exposure_share_concentrated",
        "cluster_unresolved_share_concentrated",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.rows == (
        api.MarketEventClusterExposureReportRow(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("80.0000"),
            unresolved_count=d("4"),
            exposure_share=d("0.666667"),
            unresolved_share=d("0.800000"),
            expected_resolution_window_start_at=WINDOW_START - timedelta(days=1),
            expected_resolution_window_end_at=WINDOW_END + timedelta(days=1),
            concentration_status="concentrated",
            reason_codes=(
                "cluster_exposure_share_concentrated",
                "cluster_unresolved_share_concentrated",
            ),
        ),
        api.MarketEventClusterExposureReportRow(
            cluster_id="cluster_beta",
            team="sports_team",
            category="soccer",
            paper_exposure=d("40.0000"),
            unresolved_count=d("1"),
            exposure_share=d("0.333333"),
            unresolved_share=d("0.200000"),
            expected_resolution_window_start_at=datetime(2026, 7, 6, 0, 0, tzinfo=UTC),
            expected_resolution_window_end_at=datetime(2026, 7, 7, 0, 0, tzinfo=UTC),
            concentration_status="sparse",
            reason_codes=("cluster_exposure_distribution_sparse",),
        ),
    )


def test_cluster_exposure_reports_watch_when_thresholds_are_crossed_without_concentration() -> None:
    report = _report(
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("50.0000"),
            unresolved_count=d("1"),
        ),
        _source_row(
            cluster_id="cluster_beta",
            team="sports_team",
            category="soccer",
            paper_exposure=d("50.0000"),
            unresolved_count=d("1"),
        ),
    )

    assert report.concentration_status == "watch"
    assert report.top_cluster_id == "cluster_alpha"
    assert report.top_cluster_exposure_share == d("0.500000")
    assert report.top_cluster_unresolved_share == d("0.500000")
    assert report.reason_codes == (
        "cluster_exposure_share_watch",
        "cluster_unresolved_share_watch",
    )
    assert tuple(row.cluster_id for row in report.rows) == (
        "cluster_alpha",
        "cluster_beta",
    )
    assert all(row.concentration_status == "watch" for row in report.rows)
    assert all(
        row.reason_codes
        == ("cluster_exposure_share_watch", "cluster_unresolved_share_watch")
        for row in report.rows
    )


def test_cluster_exposure_reports_empty_input_as_sparse_zeroed_report() -> None:
    report = _report()

    assert report.source_row_count == d("0")
    assert report.cluster_count == d("0")
    assert report.total_paper_exposure == d("0.0000")
    assert report.total_unresolved_count == d("0")
    assert report.top_cluster_id is None
    assert report.top_cluster_exposure_share == d("0.000000")
    assert report.top_cluster_unresolved_share == d("0.000000")
    assert report.concentration_status == "sparse"
    assert report.rows == ()
    assert report.reason_codes == ("missing_event_cluster_rows",)


def test_cluster_exposure_json_payload_is_json_ready_without_floats() -> None:
    api = _api()
    report = _report(
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("1.2500"),
            unresolved_count=d("1"),
        )
    )

    payload = api.market_event_cluster_exposure_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["total_paper_exposure"] == "1.2500"
    assert payload["total_unresolved_count"] == "1"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert payload["rows"][0]["paper_exposure"] == "1.2500"
    assert payload["rows"][0]["unresolved_count"] == "1"
    assert payload["rows"][0]["exposure_share"] == "1.000000"
    assert not any(isinstance(value, float) for value in payload.values())
    with pytest.raises(ValueError, match="int"):
        api._json_ready({"public_count": 1})


def test_cluster_exposure_derived_validation_digest_is_payload_bound() -> None:
    report = _report(
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("1.2500"),
            unresolved_count=d("1"),
        )
    )
    changed_window_report = _report(
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("1.2500"),
            unresolved_count=d("1"),
            window_end=WINDOW_END + timedelta(days=1),
        )
    )

    assert report.derived_validation_digest != changed_window_report.derived_validation_digest


def test_cluster_exposure_validates_exact_types_utc_windows_and_decimal_only_counts() -> None:
    api = _api()
    source = _source_row(
        cluster_id="cluster_alpha",
        team="macro_team",
        category="rates",
        paper_exposure=d("1.0000"),
        unresolved_count=d("1"),
    )

    class ConfigSubclass(api.MarketEventClusterExposureReportConfig):
        pass

    class RowSubclass(api.MarketEventClusterExposureSourceRow):
        pass

    with pytest.raises(ValueError, match="rows must be a list or tuple"):
        api.build_market_event_cluster_exposure_report(
            "rows",
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows must contain"):
        api.build_market_event_cluster_exposure_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows must contain"):
        api.build_market_event_cluster_exposure_report(
            (RowSubclass(**source.__dict__),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_market_event_cluster_exposure_report(
            (),
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_market_event_cluster_exposure_report(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="cluster_id must be a string"):
        _source_row(
            cluster_id=_StringSubclass("cluster_alpha"),
            team="macro_team",
            category="rates",
            paper_exposure=d("1.0000"),
            unresolved_count=d("1"),
        )
    with pytest.raises(ValueError, match="paper_exposure must be a Decimal"):
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=_DecimalSubclass("1.0000"),
            unresolved_count=d("1"),
        )
    with pytest.raises(ValueError, match="unresolved_count must be integral"):
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("1.0000"),
            unresolved_count=d("1.5"),
        )
    with pytest.raises(ValueError, match="expected_resolution_window_start_at must be timezone-aware"):
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("1.0000"),
            unresolved_count=d("1"),
            window_start=datetime(2026, 7, 5, 0, 0),
        )
    with pytest.raises(ValueError, match="expected_resolution_window_start_at must be timezone-aware"):
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("1.0000"),
            unresolved_count=d("1"),
            window_start=datetime(2026, 7, 5, 0, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="expected resolution window start must be <= end"):
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("1.0000"),
            unresolved_count=d("1"),
            window_start=WINDOW_END,
            window_end=WINDOW_START,
        )


def test_cluster_exposure_dataclasses_are_frozen_and_validate_hard_flags() -> None:
    report = _report(
        _source_row(
            cluster_id="cluster_alpha",
            team="macro_team",
            category="rates",
            paper_exposure=d("1.0000"),
            unresolved_count=d("1"),
        ),
        _source_row(
            cluster_id="cluster_beta",
            team="sports_team",
            category="soccer",
            paper_exposure=d("0.5000"),
            unresolved_count=d("1"),
        )
    )

    with pytest.raises(FrozenInstanceError):
        report.concentration_status = "sparse"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True for config"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True for report"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest must be a sha256 hex digest"):
        replace(report, derived_validation_digest="tampered")
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report rows must be sorted"):
        replace(report, rows=tuple(reversed(report.rows)))


def test_cluster_exposure_public_contract_is_decimal_only_and_hard_flagged() -> None:
    api = _api()

    public_dataclasses = (
        api.MarketEventClusterExposureReportConfig,
        api.MarketEventClusterExposureSourceRow,
        api.MarketEventClusterExposureReportRow,
        api.MarketEventClusterExposureReport,
    )

    for contract in public_dataclasses:
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type is not float for field in fields(contract))


def test_cluster_exposure_report_rejects_unsafe_live_auth_wallet_order_network_database_and_persist_surfaces() -> None:
    api = _api()

    unsafe_values = (
        {"live": True},
        {"auth": "token"},
        {"wallet": "0xabc"},
        {"order": {"side": "BUY"}},
        {"network": "polygon"},
        {"database": "postgres"},
        {"persist": True},
    )

    for unsafe_value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public payload"):
            api._json_ready(unsafe_value)
    for unsafe_text in (
        "live_ref",
        "auth_ref",
        "wallet_ref",
        "order_ref",
        "network_ref",
        "database_ref",
        "persist_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            _source_row(
                cluster_id=unsafe_text,
                team="macro_team",
                category="rates",
                paper_exposure=d("1.0000"),
                unresolved_count=d("1"),
            )
        with pytest.raises(ValueError, match="unsafe public payload"):
            api._json_ready({"safe_key": unsafe_text})


def test_cluster_exposure_module_is_report_only_without_live_or_advice_surfaces() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()

    assert "market_event_cluster_exposure_report_payload" in public_names
    assert "derived_validation_digest" in source
    for banned in (
        "recommended_next_step",
        "advice",
        "investment",
        "account",
        "broker",
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "private_key",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "os.environ",
        "open(",
        ".write(",
        ".read(",
        "socket",
    ):
        assert banned not in source
