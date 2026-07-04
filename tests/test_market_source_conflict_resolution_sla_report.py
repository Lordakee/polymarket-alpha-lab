from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_source_conflict_resolution_sla_report import (
    DEFAULT_MARKET_SOURCE_CONFLICT_RESOLUTION_SLA_REPORT_CONFIG_VERSION,
    MarketSourceConflictResolutionSlaConfig,
    MarketSourceConflictResolutionSlaInputRow,
    MarketSourceConflictResolutionSlaReport,
    build_market_source_conflict_resolution_sla_report,
    market_source_conflict_resolution_sla_report_to_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _NaiveTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _config(**overrides: object) -> MarketSourceConflictResolutionSlaConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_SOURCE_CONFLICT_RESOLUTION_SLA_REPORT_CONFIG_VERSION
        ),
        "default_resolution_sla_seconds": d("3600.000000"),
        "source_family_sla_seconds": (
            ("flow", d("1800.000000")),
            ("polling", d("5400.000000")),
        ),
    }
    values.update(overrides)
    return MarketSourceConflictResolutionSlaConfig(**values)


def _row(
    conflict_id: str,
    source_family: str,
    *,
    team_id: str = "politics",
    category_id: str = "politics",
    detected_at: datetime = GENERATED_AT,
    official_checked_at: datetime | None = GENERATED_AT,
    proxy_checked_at: datetime | None = GENERATED_AT,
    source_family_checked_at: datetime | None = GENERATED_AT,
    team_acknowledged_at: datetime | None = GENERATED_AT,
    adjudication_evidence_at: datetime | None = GENERATED_AT,
) -> MarketSourceConflictResolutionSlaInputRow:
    return MarketSourceConflictResolutionSlaInputRow(
        team_id=team_id,
        category_id=category_id,
        conflict_id=conflict_id,
        source_family=source_family,
        detected_at=detected_at,
        official_checked_at=official_checked_at,
        proxy_checked_at=proxy_checked_at,
        source_family_checked_at=source_family_checked_at,
        team_acknowledged_at=team_acknowledged_at,
        adjudication_evidence_at=adjudication_evidence_at,
    )


def _bypassed_row(
    row: MarketSourceConflictResolutionSlaInputRow,
    **overrides: object,
) -> MarketSourceConflictResolutionSlaInputRow:
    values = {field.name: getattr(row, field.name) for field in fields(row)}
    values.update(overrides)
    bypassed = object.__new__(MarketSourceConflictResolutionSlaInputRow)
    for name, value in values.items():
        object.__setattr__(bypassed, name, value)
    return bypassed


def test_report_flags_breached_conflicts_and_sorts_deterministically() -> None:
    report = build_market_source_conflict_resolution_sla_report(
        (
            _row(
                "resolved_conflict",
                "flow",
                team_id="crypto_btc",
                category_id="finance.crypto.btc",
                detected_at=GENERATED_AT - timedelta(seconds=600),
                official_checked_at=GENERATED_AT - timedelta(seconds=590),
                proxy_checked_at=GENERATED_AT - timedelta(seconds=580),
                source_family_checked_at=GENERATED_AT - timedelta(seconds=570),
                team_acknowledged_at=GENERATED_AT - timedelta(seconds=560),
                adjudication_evidence_at=GENERATED_AT - timedelta(seconds=550),
            ),
            _row(
                "pending_checks",
                "onchain",
                team_id="crypto_btc",
                category_id="finance.crypto.btc",
                detected_at=GENERATED_AT - timedelta(seconds=600),
                official_checked_at=GENERATED_AT - timedelta(seconds=580),
                proxy_checked_at=None,
                source_family_checked_at=None,
                team_acknowledged_at=None,
                adjudication_evidence_at=GENERATED_AT - timedelta(seconds=540),
            ),
            _row(
                "breach_open_missing",
                "polling",
                detected_at=GENERATED_AT - timedelta(seconds=7200),
                official_checked_at=None,
                proxy_checked_at=GENERATED_AT - timedelta(seconds=7100),
                source_family_checked_at=GENERATED_AT - timedelta(seconds=7050),
                team_acknowledged_at=GENERATED_AT - timedelta(seconds=7000),
                adjudication_evidence_at=None,
            ),
            _row(
                "breach_complete_late",
                "rules",
                detected_at=GENERATED_AT - timedelta(seconds=7200),
                official_checked_at=GENERATED_AT - timedelta(seconds=7000),
                proxy_checked_at=GENERATED_AT - timedelta(seconds=6900),
                source_family_checked_at=GENERATED_AT - timedelta(seconds=6800),
                team_acknowledged_at=GENERATED_AT - timedelta(seconds=6700),
                adjudication_evidence_at=GENERATED_AT - timedelta(seconds=600),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report == MarketSourceConflictResolutionSlaReport(
        generated_at=GENERATED_AT,
        config_version=(
            DEFAULT_MARKET_SOURCE_CONFLICT_RESOLUTION_SLA_REPORT_CONFIG_VERSION
        ),
        report_status="breached",
        conflict_count=d("4.000000"),
        breached_conflict_count=d("2.000000"),
        pending_conflict_count=d("1.000000"),
        resolved_conflict_count=d("1.000000"),
        missing_official_check_count=d("1.000000"),
        missing_proxy_check_count=d("1.000000"),
        missing_source_family_check_count=d("1.000000"),
        missing_team_acknowledgement_count=d("1.000000"),
        missing_adjudication_evidence_count=d("1.000000"),
        breach_ratio=d("0.500000"),
        oldest_conflict_age_seconds=d("7200.000000"),
        rows=report.rows,
        reason_codes=(
            "market_source_conflict_resolution_sla_breached",
            "market_source_conflict_resolution_sla_pending",
            "market_source_conflict_resolution_missing_official_check",
            "market_source_conflict_resolution_missing_proxy_check",
            "market_source_conflict_resolution_missing_source_family_check",
            "market_source_conflict_resolution_missing_team_acknowledgement",
            "market_source_conflict_resolution_missing_adjudication_evidence",
            "market_source_conflict_resolution_late_completion",
            "market_source_conflict_resolution_open_beyond_sla",
        ),
    )
    assert tuple(row.conflict_id for row in report.rows) == (
        "breach_open_missing",
        "breach_complete_late",
        "pending_checks",
        "resolved_conflict",
    )
    assert tuple(row.sla_status for row in report.rows) == (
        "breached",
        "breached",
        "pending",
        "resolved",
    )

    open_breach = report.rows[0]
    assert open_breach.sla_seconds == d("5400.000000")
    assert open_breach.required_evidence_count == d("5.000000")
    assert open_breach.completed_evidence_count == d("3.000000")
    assert open_breach.missing_evidence_count == d("2.000000")
    assert open_breach.evidence_completion_ratio == d("0.600000")
    assert open_breach.age_seconds == d("7200.000000")
    assert open_breach.resolution_age_seconds is None
    assert open_breach.seconds_over_sla == d("1800.000000")
    assert open_breach.reason_codes == (
        "market_source_conflict_resolution_sla_breached",
        "market_source_conflict_resolution_missing_official_check",
        "market_source_conflict_resolution_missing_adjudication_evidence",
        "market_source_conflict_resolution_open_beyond_sla",
    )

    late_completion = report.rows[1]
    assert late_completion.sla_seconds == d("3600.000000")
    assert late_completion.resolution_age_seconds == d("6600.000000")
    assert late_completion.seconds_over_sla == d("3000.000000")
    assert late_completion.reason_codes == (
        "market_source_conflict_resolution_sla_breached",
        "market_source_conflict_resolution_late_completion",
    )

    pending = report.rows[2]
    assert pending.sla_status == "pending"
    assert pending.reason_codes == (
        "market_source_conflict_resolution_sla_pending",
        "market_source_conflict_resolution_missing_proxy_check",
        "market_source_conflict_resolution_missing_source_family_check",
        "market_source_conflict_resolution_missing_team_acknowledgement",
    )
    assert pending.seconds_over_sla == d("0.000000")

    resolved = report.rows[3]
    assert resolved.sla_status == "resolved"
    assert resolved.reason_codes == (
        "market_source_conflict_resolution_sla_clear",
    )
    assert resolved.evidence_completion_ratio == d("1.000000")

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_report_returns_clear_empty_report() -> None:
    report = build_market_source_conflict_resolution_sla_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "clear"
    assert report.conflict_count == d("0.000000")
    assert report.breached_conflict_count == d("0.000000")
    assert report.pending_conflict_count == d("0.000000")
    assert report.resolved_conflict_count == d("0.000000")
    assert report.breach_ratio == d("0.000000")
    assert report.oldest_conflict_age_seconds is None
    assert report.rows == ()
    assert report.reason_codes == ("market_source_conflict_resolution_sla_clear",)


def test_json_ready_payload_uses_strings_for_decimal_and_utc_datetimes() -> None:
    report = build_market_source_conflict_resolution_sla_report(
        (
            _row(
                "breach_open_missing",
                "polling",
                detected_at=GENERATED_AT - timedelta(seconds=7200),
                official_checked_at=None,
                adjudication_evidence_at=None,
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    ready = market_source_conflict_resolution_sla_report_to_payload(report)

    assert ready["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert ready["conflict_count"] == "1.000000"
    assert ready["breach_ratio"] == "1.000000"
    assert ready["paper_only"] is True
    assert ready["rows"][0]["detected_at"] == "2026-07-02T10:00:00+00:00"
    assert ready["rows"][0]["age_seconds"] == "7200.000000"
    assert ready["rows"][0]["resolution_age_seconds"] is None
    assert ready["rows"][0]["paper_only"] is True

    rendered = repr(ready).lower()
    for token in (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ):
        assert token not in rendered


def test_dataclasses_are_frozen_and_use_decimal_only_metrics() -> None:
    report = build_market_source_conflict_resolution_sla_report(
        (
            _row(
                "resolved_conflict",
                "flow",
                team_id="crypto_btc",
                category_id="finance.crypto.btc",
                detected_at=GENERATED_AT - timedelta(seconds=600),
                official_checked_at=GENERATED_AT - timedelta(seconds=590),
                proxy_checked_at=GENERATED_AT - timedelta(seconds=580),
                source_family_checked_at=GENERATED_AT - timedelta(seconds=570),
                team_acknowledged_at=GENERATED_AT - timedelta(seconds=560),
                adjudication_evidence_at=GENERATED_AT - timedelta(seconds=550),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.rows[0].sla_status = "breached"

    metric_names = (
        "conflict_count",
        "breached_conflict_count",
        "pending_conflict_count",
        "resolved_conflict_count",
        "missing_official_check_count",
        "missing_proxy_check_count",
        "missing_source_family_check_count",
        "missing_team_acknowledgement_count",
        "missing_adjudication_evidence_count",
        "breach_ratio",
        "oldest_conflict_age_seconds",
    )
    for name in metric_names:
        value = getattr(report, name)
        if value is not None:
            assert type(value) is Decimal

    row_metric_names = (
        "sla_seconds",
        "required_evidence_count",
        "completed_evidence_count",
        "missing_evidence_count",
        "evidence_completion_ratio",
        "age_seconds",
        "resolution_age_seconds",
        "seconds_over_sla",
    )
    for name in row_metric_names:
        value = getattr(report.rows[0], name)
        if value is not None:
            assert type(value) is Decimal


def test_rejects_non_decimal_naive_future_and_non_readonly_inputs() -> None:
    with pytest.raises(ValueError, match="default_resolution_sla_seconds"):
        MarketSourceConflictResolutionSlaConfig(default_resolution_sla_seconds=3600)
    with pytest.raises(ValueError, match="source_family_sla_seconds"):
        MarketSourceConflictResolutionSlaConfig(
            source_family_sla_seconds=(("flow", _DecimalSubclass("1.000000")),),
        )
    with pytest.raises(ValueError, match="paper_only"):
        MarketSourceConflictResolutionSlaConfig(paper_only=False)
    with pytest.raises(ValueError, match="detected_at"):
        _row(
            "naive_time",
            "flow",
            detected_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _row(
            "naive_like_tzinfo",
            "flow",
            detected_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NaiveTz()),
        )
    with pytest.raises(ValueError, match="source_family"):
        _row("unsafe_family", _join_parts("wal", "let"))
    with pytest.raises(ValueError, match="conflict_id"):
        _row(_join_parts("re", "place"), "flow")
    with pytest.raises(ValueError, match="source_family"):
        _row("unsafe_family_repl", _join_parts("re", "place"))

    with pytest.raises(ValueError, match="readonly"):
        replace(
            _row(
                "not_readonly",
                "flow",
                detected_at=GENERATED_AT - timedelta(seconds=60),
            ),
            readonly=False,
        )

    malformed = _bypassed_row(
        _row(
            "bypassed_readonly",
            "flow",
            detected_at=GENERATED_AT - timedelta(seconds=60),
        ),
        readonly=False,
    )
    with pytest.raises(ValueError, match="readonly"):
        build_market_source_conflict_resolution_sla_report(
            (malformed,),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="input rows"):
        build_market_source_conflict_resolution_sla_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        build_market_source_conflict_resolution_sla_report(
            (
                _row(
                    "future_check",
                    "flow",
                    detected_at=GENERATED_AT - timedelta(seconds=10),
                    official_checked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="detected_at"):
        build_market_source_conflict_resolution_sla_report(
            (
                _row(
                    "before_detection",
                    "flow",
                    detected_at=GENERATED_AT - timedelta(seconds=10),
                    official_checked_at=GENERATED_AT - timedelta(seconds=11),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="conflict_id"):
        build_market_source_conflict_resolution_sla_report(
            (
                _row("duplicate_conflict", "flow"),
                _row("duplicate_conflict", "polling"),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_module_has_no_file_network_or_live_action_surfaces() -> None:
    import polymarket_alpha_lab.market_source_conflict_resolution_sla_report as api

    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert "float(" not in source
    assert ".total_seconds(" not in source
    for token in (
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ):
        assert token not in source

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
                "delete",
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

    exposed_names = {field.name for field in fields(MarketSourceConflictResolutionSlaReport)}
    assert _join_parts("pay", "load") not in exposed_names
