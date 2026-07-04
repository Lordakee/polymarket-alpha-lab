from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from json import dumps

import pytest

from polymarket_alpha_lab.market_source_family_divergence_sla_report import (
    DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_SLA_CONFIG_VERSION,
    MarketSourceFamilyDivergenceSlaConfig,
    MarketSourceFamilyDivergenceSlaInputRow,
    MarketSourceFamilyDivergenceSlaReport,
    MarketSourceFamilyDivergenceSlaReportRow,
    build_market_source_family_divergence_sla_report,
    market_source_family_divergence_sla_report_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> MarketSourceFamilyDivergenceSlaConfig:
    values = {
        "config_version": DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_SLA_CONFIG_VERSION,
        "divergence_resolution_sla_seconds": d("3600.000000"),
        "official_source_freshness_sla_seconds": d("1800.000000"),
        "team_acknowledgement_sla_seconds": d("900.000000"),
    }
    values.update(overrides)
    return MarketSourceFamilyDivergenceSlaConfig(**values)


def _row(
    case_id: str,
    source_family: str,
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    divergence_detected_at: datetime = GENERATED_AT - timedelta(minutes=10),
    divergence_resolved_at: datetime | None = None,
    official_source_observed_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    proxy_confirmed_at: datetime | None = None,
    official_source_confirmed_at: datetime | None = GENERATED_AT - timedelta(minutes=4),
    owner_id: str | None = "data_steward",
    team_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=2),
) -> MarketSourceFamilyDivergenceSlaInputRow:
    return MarketSourceFamilyDivergenceSlaInputRow(
        team_id=team_id,
        category_id=category_id,
        source_family=source_family,
        case_id=case_id,
        divergence_detected_at=divergence_detected_at,
        divergence_resolved_at=divergence_resolved_at,
        official_source_observed_at=official_source_observed_at,
        proxy_confirmed_at=proxy_confirmed_at,
        official_source_confirmed_at=official_source_confirmed_at,
        owner_id=owner_id,
        team_acknowledged_at=team_acknowledged_at,
    )


def test_divergence_sla_report_flags_queue_reasons_and_sorts_deterministically() -> None:
    report = build_market_source_family_divergence_sla_report(
        (
            _row(
                "case_watch_ack",
                "exchange",
                divergence_detected_at=GENERATED_AT - timedelta(minutes=20),
                team_acknowledged_at=None,
            ),
            _row(
                "case_ready",
                "flow",
                divergence_detected_at=GENERATED_AT - timedelta(minutes=8),
            ),
            _row(
                "case_blocked",
                "oracle",
                divergence_detected_at=GENERATED_AT - timedelta(hours=2),
                official_source_observed_at=GENERATED_AT - timedelta(hours=3),
                proxy_confirmed_at=GENERATED_AT - timedelta(minutes=30),
                official_source_confirmed_at=None,
                owner_id=None,
                team_acknowledged_at=GENERATED_AT - timedelta(hours=1),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketSourceFamilyDivergenceSlaReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_SLA_CONFIG_VERSION
    )
    assert report.sla_status == "blocked"
    assert report.queue_item_count == d("3.000000")
    assert report.ready_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.overdue_resolution_count == d("1.000000")
    assert report.stale_official_source_count == d("1.000000")
    assert report.proxy_only_confirmation_count == d("1.000000")
    assert report.missing_owner_count == d("1.000000")
    assert report.acknowledgement_lag_count == d("2.000000")
    assert report.blocked_ratio == d("0.333333")
    assert report.watch_ratio == d("0.333333")
    assert report.reason_codes == (
        "source_family_divergence_resolution_overdue",
        "source_family_divergence_official_source_stale",
        "source_family_divergence_proxy_only_confirmation",
        "source_family_divergence_missing_owner",
        "source_family_divergence_acknowledgement_lag",
    )
    assert tuple(row.case_id for row in report.rows) == (
        "case_blocked",
        "case_watch_ack",
        "case_ready",
    )

    blocked = report.rows[0]
    assert blocked == MarketSourceFamilyDivergenceSlaReportRow(
        category_id="finance.crypto.btc",
        team_id="crypto_btc",
        source_family="oracle",
        case_id="case_blocked",
        row_status="blocked",
        divergence_age_seconds=d("7200.000000"),
        official_source_age_seconds=d("10800.000000"),
        acknowledgement_lag_seconds=d("3600.000000"),
        reason_codes=(
            "source_family_divergence_resolution_overdue",
            "source_family_divergence_official_source_stale",
            "source_family_divergence_proxy_only_confirmation",
            "source_family_divergence_missing_owner",
            "source_family_divergence_acknowledgement_lag",
        ),
    )
    assert report.rows[1].row_status == "watch"
    assert report.rows[1].reason_codes == (
        "source_family_divergence_acknowledgement_lag",
    )
    assert report.rows[2].row_status == "ready"
    assert report.rows[2].reason_codes == ("source_family_divergence_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_divergence_sla_report_returns_ready_empty_report() -> None:
    report = build_market_source_family_divergence_sla_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.sla_status == "ready"
    assert report.queue_item_count == d("0.000000")
    assert report.ready_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.blocked_ratio == d("0.000000")
    assert report.watch_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("source_family_divergence_ready",)


def test_divergence_sla_payload_is_json_ready_without_floats_or_unsafe_surface() -> None:
    report = build_market_source_family_divergence_sla_report(
        (
            _row(
                "case_payload",
                "exchange",
                divergence_detected_at=GENERATED_AT - timedelta(seconds=1, microseconds=500000),
                official_source_observed_at=GENERATED_AT
                - timedelta(seconds=1, microseconds=250000),
                team_acknowledged_at=GENERATED_AT - timedelta(seconds=1),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = market_source_family_divergence_sla_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["queue_item_count"] == "1.000000"
    assert payload["blocked_ratio"] == "0.000000"
    assert payload["rows"][0]["divergence_age_seconds"] == "1.500000"
    assert payload["rows"][0]["official_source_age_seconds"] == "1.250000"
    assert payload["rows"][0]["acknowledgement_lag_seconds"] == "0.500000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _has_float(payload) is False
    dumps(payload)

    public = repr(payload).lower()
    for token in (
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
        "auth",
    ):
        assert token not in public


def test_divergence_sla_validates_utc_decimal_flags_and_freezes_rows() -> None:
    with pytest.raises(ValueError, match="divergence_resolution_sla_seconds"):
        MarketSourceFamilyDivergenceSlaConfig(
            divergence_resolution_sla_seconds=3600,
        )
    with pytest.raises(ValueError, match="official_source_freshness_sla_seconds"):
        MarketSourceFamilyDivergenceSlaConfig(
            official_source_freshness_sla_seconds=_DecimalSubclass("1800.000000"),
        )
    with pytest.raises(ValueError, match="team_acknowledgement_sla_seconds"):
        MarketSourceFamilyDivergenceSlaConfig(
            team_acknowledgement_sla_seconds=d("900"),
        )
    with pytest.raises(ValueError, match="config_version"):
        MarketSourceFamilyDivergenceSlaConfig(
            config_version=_StringSubclass(
                DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_SLA_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_source_family_divergence_sla_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_source_family_divergence_sla_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="future"):
        build_market_source_family_divergence_sla_report(
            (
                _row(
                    "future_case",
                    "flow",
                    divergence_detected_at=GENERATED_AT + timedelta(seconds=1),
                    team_acknowledged_at=None,
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="divergence_resolved_at"):
        _row(
            "bad_resolution_time",
            "flow",
            divergence_resolved_at=GENERATED_AT - timedelta(minutes=20),
        )
    with pytest.raises(ValueError, match="team_acknowledged_at"):
        _row(
            "bad_ack_time",
            "flow",
            team_acknowledged_at=GENERATED_AT - timedelta(minutes=20),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_row("not_paper", "flow"), paper_only=False)
    with pytest.raises(ValueError, match="input rows"):
        build_market_source_family_divergence_sla_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    report = build_market_source_family_divergence_sla_report(
        (_row("frozen_case", "flow"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.rows[0].row_status = "blocked"

    with pytest.raises(ValueError, match="reason_codes"):
        MarketSourceFamilyDivergenceSlaReportRow(
            category_id="finance.crypto.btc",
            team_id="crypto_btc",
            source_family="flow",
            case_id="case_empty_reason",
            row_status="watch",
            divergence_age_seconds=d("60.000000"),
            official_source_age_seconds=d("30.000000"),
            acknowledgement_lag_seconds=d("10.000000"),
            reason_codes=(),
        )


def test_divergence_sla_direct_report_validation_rejects_inconsistent_rows() -> None:
    row = MarketSourceFamilyDivergenceSlaReportRow(
        category_id="finance.crypto.btc",
        team_id="crypto_btc",
        source_family="flow",
        case_id="case_direct",
        row_status="ready",
        divergence_age_seconds=d("60.000000"),
        official_source_age_seconds=d("30.000000"),
        acknowledgement_lag_seconds=d("10.000000"),
        reason_codes=("source_family_divergence_ready",),
    )

    with pytest.raises(ValueError, match="queue_item_count"):
        MarketSourceFamilyDivergenceSlaReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_SLA_CONFIG_VERSION,
            sla_status="ready",
            queue_item_count=d("2.000000"),
            ready_count=d("1.000000"),
            watch_count=d("0.000000"),
            blocked_count=d("0.000000"),
            overdue_resolution_count=d("0.000000"),
            stale_official_source_count=d("0.000000"),
            proxy_only_confirmation_count=d("0.000000"),
            missing_owner_count=d("0.000000"),
            acknowledgement_lag_count=d("0.000000"),
            blocked_ratio=d("0.000000"),
            watch_ratio=d("0.000000"),
            rows=(row,),
            reason_codes=("source_family_divergence_ready",),
        )


def test_divergence_sla_module_scope_excludes_io_and_mutation_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_source_family_divergence_sla_report",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

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
        "broker",
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


def _has_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_has_float(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_has_float(item) for item in value)
    return False
