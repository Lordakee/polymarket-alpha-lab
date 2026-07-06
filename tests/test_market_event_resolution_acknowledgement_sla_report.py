from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _api():
    return import_module(
        "polymarket_alpha_lab.market_event_resolution_acknowledgement_sla_report",
    )


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_MARKET_EVENT_RESOLUTION_ACKNOWLEDGEMENT_SLA_REPORT_CONFIG_VERSION
        ),
        "default_acknowledgement_sla_seconds": d("1800.000000"),
        "market_family_acknowledgement_sla_seconds": (
            ("election-rules", d("2400.000000")),
            ("fed-policy", d("1800.000000")),
        ),
        "official_check_stale_seconds": d("900.000000"),
        "postmortem_acknowledgement_sla_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return api.MarketEventResolutionAcknowledgementSlaConfig(**values)


def _row(
    event_id: str = "resolution-public-1",
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    market_family: str = "btc-etf",
    event_resolved_at: datetime = GENERATED_AT - timedelta(minutes=20),
    official_checked_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    resolution_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=10),
    conflict_status: str = "none",
    conflict_detected_at: datetime | None = None,
    postmortem_required: bool = True,
    postmortem_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
) -> object:
    return _api().MarketEventResolutionAcknowledgementSlaInputRow(
        team_id=team_id,
        category_id=category_id,
        market_family=market_family,
        event_id=event_id,
        event_resolved_at=event_resolved_at,
        official_checked_at=official_checked_at,
        resolution_acknowledged_at=resolution_acknowledged_at,
        conflict_status=conflict_status,
        conflict_detected_at=conflict_detected_at,
        postmortem_required=postmortem_required,
        postmortem_acknowledged_at=postmortem_acknowledged_at,
    )


def _report(*rows: object, **config_overrides: object) -> object:
    return _api().build_market_event_resolution_acknowledgement_sla_report(
        rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _bypassed_row(row: object, **overrides: object) -> object:
    values = {field.name: getattr(row, field.name) for field in fields(row)}
    values.update(overrides)
    bypassed = object.__new__(
        _api().MarketEventResolutionAcknowledgementSlaInputRow,
    )
    for name, value in values.items():
        object.__setattr__(bypassed, name, value)
    return bypassed


def test_event_resolution_acknowledgement_sla_flags_exceptions_and_summaries() -> None:
    api = _api()

    report = _report(
        _row(
            "clear-resolution",
            event_resolved_at=GENERATED_AT - timedelta(seconds=1200),
            official_checked_at=GENERATED_AT - timedelta(seconds=300),
            resolution_acknowledged_at=GENERATED_AT - timedelta(seconds=600),
            postmortem_acknowledged_at=GENERATED_AT - timedelta(seconds=300),
        ),
        _row(
            "unresolved-old",
            team_id="politics",
            category_id="politics",
            market_family="election-rules",
            event_resolved_at=GENERATED_AT - timedelta(seconds=7200),
            official_checked_at=None,
            resolution_acknowledged_at=None,
            conflict_status="unresolved",
            conflict_detected_at=GENERATED_AT - timedelta(seconds=7100),
            postmortem_acknowledged_at=None,
        ),
        _row(
            "late-ack-stale-official",
            team_id="macro_rates",
            category_id="finance.macro.rates",
            market_family="fed-policy",
            event_resolved_at=GENERATED_AT - timedelta(seconds=4000),
            official_checked_at=GENERATED_AT - timedelta(seconds=2000),
            resolution_acknowledged_at=GENERATED_AT - timedelta(seconds=1800),
            postmortem_required=False,
            postmortem_acknowledged_at=None,
        ),
        _row(
            "pending-fresh",
            team_id="sports_soccer",
            category_id="sports.soccer",
            market_family="world-cup",
            event_resolved_at=GENERATED_AT - timedelta(seconds=600),
            official_checked_at=GENERATED_AT - timedelta(seconds=100),
            resolution_acknowledged_at=None,
            postmortem_acknowledged_at=None,
        ),
    )

    assert type(report) is api.MarketEventResolutionAcknowledgementSlaReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_MARKET_EVENT_RESOLUTION_ACKNOWLEDGEMENT_SLA_REPORT_CONFIG_VERSION
    )
    assert report.report_status == "breached"
    assert report.reason_codes == (
        "market_event_resolution_acknowledgement_sla_breached",
        "market_event_resolution_acknowledgement_sla_pending",
        "market_event_resolution_acknowledgement_missing",
        "market_event_resolution_acknowledgement_late",
        "market_event_resolution_official_check_missing",
        "market_event_resolution_official_check_stale",
        "market_event_resolution_unresolved_conflict",
        "market_event_resolution_postmortem_acknowledgement_missing",
    )
    assert report.event_count == d("4.000000")
    assert report.acknowledged_event_count == d("1.000000")
    assert report.pending_event_count == d("1.000000")
    assert report.breached_event_count == d("2.000000")
    assert report.exception_count == d("3.000000")
    assert report.sla_breach_count == d("2.000000")
    assert report.missing_acknowledgement_count == d("2.000000")
    assert report.missing_official_check_count == d("1.000000")
    assert report.stale_official_check_count == d("1.000000")
    assert report.unresolved_conflict_count == d("1.000000")
    assert report.missing_postmortem_acknowledgement_count == d("2.000000")
    assert report.exception_ratio == d("0.750000")
    assert report.max_resolution_age_seconds == d("7200.000000")

    assert tuple(row.event_id for row in report.rows) == (
        "unresolved-old",
        "late-ack-stale-official",
        "pending-fresh",
        "clear-resolution",
    )
    assert tuple(row.acknowledgement_status for row in report.rows) == (
        "breached",
        "breached",
        "pending",
        "acknowledged",
    )

    unresolved = report.rows[0]
    assert unresolved.acknowledgement_sla_seconds == d("2400.000000")
    assert unresolved.resolution_age_seconds == d("7200.000000")
    assert unresolved.acknowledgement_age_seconds == d("7200.000000")
    assert unresolved.official_check_age_seconds is None
    assert unresolved.postmortem_acknowledgement_age_seconds == d("7200.000000")
    assert unresolved.breach_seconds == d("4800.000000")
    assert unresolved.reason_codes == (
        "market_event_resolution_acknowledgement_sla_breached",
        "market_event_resolution_acknowledgement_missing",
        "market_event_resolution_official_check_missing",
        "market_event_resolution_unresolved_conflict",
        "market_event_resolution_postmortem_acknowledgement_missing",
    )

    late = report.rows[1]
    assert late.acknowledgement_sla_seconds == d("1800.000000")
    assert late.acknowledgement_age_seconds == d("2200.000000")
    assert late.official_check_age_seconds == d("2000.000000")
    assert late.breach_seconds == d("400.000000")
    assert late.reason_codes == (
        "market_event_resolution_acknowledgement_sla_breached",
        "market_event_resolution_acknowledgement_late",
        "market_event_resolution_official_check_stale",
    )

    pending = report.rows[2]
    assert pending.acknowledgement_age_seconds == d("600.000000")
    assert pending.breach_seconds == d("0.000000")
    assert pending.reason_codes == (
        "market_event_resolution_acknowledgement_sla_pending",
        "market_event_resolution_acknowledgement_missing",
        "market_event_resolution_postmortem_acknowledgement_missing",
    )

    clear = report.rows[3]
    assert clear.reason_codes == ("market_event_resolution_acknowledgement_sla_clear",)

    assert report.market_family_summary_rows == (
        api.MarketEventResolutionAcknowledgementSlaSummaryRow(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            market_family="btc-etf",
            report_status="clear",
            event_count=d("1.000000"),
            exception_count=d("0.000000"),
            sla_breach_count=d("0.000000"),
            stale_official_check_count=d("0.000000"),
            missing_official_check_count=d("0.000000"),
            unresolved_conflict_count=d("0.000000"),
            missing_postmortem_acknowledgement_count=d("0.000000"),
            exception_ratio=d("0.000000"),
            max_resolution_age_seconds=d("1200.000000"),
            reason_codes=("market_event_resolution_acknowledgement_sla_clear",),
        ),
        api.MarketEventResolutionAcknowledgementSlaSummaryRow(
            team_id="macro_rates",
            category_id="finance.macro.rates",
            market_family="fed-policy",
            report_status="breached",
            event_count=d("1.000000"),
            exception_count=d("1.000000"),
            sla_breach_count=d("1.000000"),
            stale_official_check_count=d("1.000000"),
            missing_official_check_count=d("0.000000"),
            unresolved_conflict_count=d("0.000000"),
            missing_postmortem_acknowledgement_count=d("0.000000"),
            exception_ratio=d("1.000000"),
            max_resolution_age_seconds=d("4000.000000"),
            reason_codes=(
                "market_event_resolution_acknowledgement_sla_breached",
                "market_event_resolution_acknowledgement_late",
                "market_event_resolution_official_check_stale",
            ),
        ),
        api.MarketEventResolutionAcknowledgementSlaSummaryRow(
            team_id="politics",
            category_id="politics",
            market_family="election-rules",
            report_status="breached",
            event_count=d("1.000000"),
            exception_count=d("1.000000"),
            sla_breach_count=d("1.000000"),
            stale_official_check_count=d("0.000000"),
            missing_official_check_count=d("1.000000"),
            unresolved_conflict_count=d("1.000000"),
            missing_postmortem_acknowledgement_count=d("1.000000"),
            exception_ratio=d("1.000000"),
            max_resolution_age_seconds=d("7200.000000"),
            reason_codes=(
                "market_event_resolution_acknowledgement_sla_breached",
                "market_event_resolution_acknowledgement_missing",
                "market_event_resolution_official_check_missing",
                "market_event_resolution_unresolved_conflict",
                "market_event_resolution_postmortem_acknowledgement_missing",
            ),
        ),
        api.MarketEventResolutionAcknowledgementSlaSummaryRow(
            team_id="sports_soccer",
            category_id="sports.soccer",
            market_family="world-cup",
            report_status="watch",
            event_count=d("1.000000"),
            exception_count=d("1.000000"),
            sla_breach_count=d("0.000000"),
            stale_official_check_count=d("0.000000"),
            missing_official_check_count=d("0.000000"),
            unresolved_conflict_count=d("0.000000"),
            missing_postmortem_acknowledgement_count=d("1.000000"),
            exception_ratio=d("1.000000"),
            max_resolution_age_seconds=d("600.000000"),
            reason_codes=(
                "market_event_resolution_acknowledgement_sla_pending",
                "market_event_resolution_acknowledgement_missing",
                "market_event_resolution_postmortem_acknowledgement_missing",
            ),
        ),
    )
    assert len(report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in report.derived_validation_digest
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_event_resolution_acknowledgement_sla_empty_report_is_clear() -> None:
    api = _api()

    report = _report()

    assert report == api.MarketEventResolutionAcknowledgementSlaReport(
        generated_at=GENERATED_AT,
        config_version=(
            api.DEFAULT_MARKET_EVENT_RESOLUTION_ACKNOWLEDGEMENT_SLA_REPORT_CONFIG_VERSION
        ),
        report_status="clear",
        reason_codes=("market_event_resolution_acknowledgement_sla_clear",),
        event_count=d("0.000000"),
        acknowledged_event_count=d("0.000000"),
        pending_event_count=d("0.000000"),
        breached_event_count=d("0.000000"),
        exception_count=d("0.000000"),
        sla_breach_count=d("0.000000"),
        missing_acknowledgement_count=d("0.000000"),
        stale_official_check_count=d("0.000000"),
        missing_official_check_count=d("0.000000"),
        unresolved_conflict_count=d("0.000000"),
        missing_postmortem_acknowledgement_count=d("0.000000"),
        exception_ratio=d("0.000000"),
        max_resolution_age_seconds=d("0.000000"),
        rows=(),
        market_family_summary_rows=(),
    )
    assert len(report.derived_validation_digest) == 64


def test_event_resolution_acknowledgement_sla_payload_is_json_ready() -> None:
    api = _api()
    report = _report(
        _row(
            "payload-old",
            team_id="politics",
            category_id="politics",
            market_family="election-rules",
            event_resolved_at=GENERATED_AT - timedelta(seconds=7200),
            official_checked_at=None,
            resolution_acknowledged_at=None,
            conflict_status="unresolved",
            conflict_detected_at=GENERATED_AT - timedelta(seconds=7100),
            postmortem_acknowledged_at=None,
        ),
    )

    payload = api.market_event_resolution_acknowledgement_sla_report_to_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["exception_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["event_resolved_at"] == "2026-07-02T10:00:00+00:00"
    assert payload["rows"][0]["resolution_age_seconds"] == "7200.000000"
    assert payload["rows"][0]["official_check_age_seconds"] is None
    assert payload["market_family_summary_rows"][0]["market_family"] == "election-rules"
    assert (
        api.validate_market_event_resolution_acknowledgement_sla_public_payload(payload)
        is True
    )

    def walk(value: object) -> tuple[object, ...]:
        if isinstance(value, dict):
            items: list[object] = []
            for child in value.values():
                items.extend(walk(child))
            return tuple(items)
        if isinstance(value, list):
            items = []
            for child in value:
                items.extend(walk(child))
            return tuple(items)
        return (value,)

    assert not any(isinstance(value, float) for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))
    assert not any(type(value) is Decimal for value in walk(payload))
    with pytest.raises(ValueError, match="report must be"):
        api.market_event_resolution_acknowledgement_sla_report_to_payload(object())

    bypassed = object.__new__(api.MarketEventResolutionAcknowledgementSlaReport)
    for field in fields(report):
        object.__setattr__(bypassed, field.name, getattr(report, field.name))
    object.__setattr__(bypassed, "event_count", 1)
    with pytest.raises(ValueError, match="event_count"):
        api.market_event_resolution_acknowledgement_sla_report_to_payload(bypassed)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["event_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_market_event_resolution_acknowledgement_sla_public_payload(
            tampered_payload,
        )

    missing_digest_payload = dict(payload)
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_market_event_resolution_acknowledgement_sla_public_payload(
            missing_digest_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["event_count"] = d("1.000000")
    with pytest.raises(ValueError, match="Decimal strings"):
        api.validate_market_event_resolution_acknowledgement_sla_public_payload(
            numeric_payload,
        )


@pytest.mark.parametrize(
    "unsafe_text",
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
    ),
)
def test_event_resolution_acknowledgement_sla_rejects_unsafe_public_surfaces(
    unsafe_text: str,
) -> None:
    api = _api()
    report = _report(_row("unsafe-public-surface"))
    payload = api.market_event_resolution_acknowledgement_sla_report_to_payload(report)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[f"{unsafe_text}_field"] = "blocked"
    with pytest.raises(ValueError, match="unsafe"):
        api.validate_market_event_resolution_acknowledgement_sla_public_payload(
            unsafe_key_payload,
        )

    with pytest.raises(ValueError, match="unsafe"):
        _row(f"{unsafe_text}-event")


def test_event_resolution_acknowledgement_sla_validates_types_times_and_flags() -> None:
    api = _api()
    offset = timezone(timedelta(hours=-4))
    report = api.build_market_event_resolution_acknowledgement_sla_report(
        (
            _row(
                "offset-resolution",
                event_resolved_at=datetime(2026, 7, 2, 7, 0, tzinfo=offset),
                official_checked_at=datetime(2026, 7, 2, 7, 15, tzinfo=offset),
                resolution_acknowledged_at=datetime(2026, 7, 2, 7, 20, tzinfo=offset),
                postmortem_acknowledged_at=datetime(2026, 7, 2, 7, 30, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].event_resolved_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert report.rows[0].resolution_age_seconds == d("3600.000000")

    with pytest.raises(FrozenInstanceError):
        report.rows[0].acknowledgement_status = "breached"  # type: ignore[misc]
    with pytest.raises(ValueError, match="official_check_age_seconds"):
        replace(report.rows[0], official_check_age_seconds=d("1.000000"))
    with pytest.raises(ValueError, match="breach_seconds"):
        replace(report.rows[0], breach_seconds=d("1.000000"))
    with pytest.raises(ValueError, match="market_family_summary_rows"):
        replace(report, market_family_summary_rows=())
    with pytest.raises(ValueError, match="default_acknowledgement_sla_seconds"):
        _config(default_acknowledgement_sla_seconds=1800)
    with pytest.raises(ValueError, match="official_check_stale_seconds"):
        _config(official_check_stale_seconds=_DecimalSubclass("900.000000"))
    with pytest.raises(ValueError, match="event_resolved_at"):
        _row("naive-resolution", event_resolved_at=datetime(2026, 7, 2, 11, 0))
    with pytest.raises(ValueError, match="event_resolved_at"):
        _row(
            "subclass-resolution",
            event_resolved_at=_DateTimeSubclass(2026, 7, 2, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="event_resolved_at"):
        _row(
            "none-offset-resolution",
            event_resolved_at=datetime(2026, 7, 2, 11, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_market_event_resolution_acknowledgement_sla_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="postmortem_required"):
        _row("bad-bool", postmortem_required=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_family"):
        _row("unsafe-family", market_family=_join_parts("wal", "let"))
    with pytest.raises(ValueError, match="report_only"):
        replace(_row("flag-row"), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="future"):
        _report(
            _row(
                "future-official",
                official_checked_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="event_resolved_at"):
        _row(
            "ack-before-resolution",
            event_resolved_at=GENERATED_AT - timedelta(seconds=100),
            resolution_acknowledged_at=GENERATED_AT - timedelta(seconds=101),
        )
    with pytest.raises(ValueError, match="conflict_detected_at"):
        _row(
            "unresolved-without-time",
            conflict_status="unresolved",
            conflict_detected_at=None,
        )
    with pytest.raises(ValueError, match="event_id"):
        _report(_row("duplicate-event"), _row("duplicate-event"))

    malformed = _bypassed_row(_row("bypassed"), paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        api.build_market_event_resolution_acknowledgement_sla_report(
            (malformed,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_event_resolution_acknowledgement_sla_decimal_only_metrics() -> None:
    report = _report(
        _row(
            "decimal-row",
            event_resolved_at=GENERATED_AT - timedelta(seconds=1800),
            official_checked_at=GENERATED_AT - timedelta(seconds=300),
            resolution_acknowledged_at=None,
            postmortem_acknowledged_at=None,
        ),
    )

    report_metric_names = (
        "event_count",
        "acknowledged_event_count",
        "pending_event_count",
        "breached_event_count",
        "exception_count",
        "sla_breach_count",
        "missing_acknowledgement_count",
        "stale_official_check_count",
        "missing_official_check_count",
        "unresolved_conflict_count",
        "missing_postmortem_acknowledgement_count",
        "exception_ratio",
        "max_resolution_age_seconds",
    )
    for name in report_metric_names:
        assert type(getattr(report, name)) is Decimal

    row_metric_names = (
        "acknowledgement_sla_seconds",
        "official_check_stale_seconds",
        "postmortem_acknowledgement_sla_seconds",
        "resolution_age_seconds",
        "acknowledgement_age_seconds",
        "official_check_age_seconds",
        "postmortem_acknowledgement_age_seconds",
        "breach_seconds",
    )
    for name in row_metric_names:
        value = getattr(report.rows[0], name)
        if value is not None:
            assert type(value) is Decimal

    summary_metric_names = (
        "event_count",
        "exception_count",
        "sla_breach_count",
        "stale_official_check_count",
        "missing_official_check_count",
        "unresolved_conflict_count",
        "missing_postmortem_acknowledgement_count",
        "exception_ratio",
        "max_resolution_age_seconds",
    )
    for name in summary_metric_names:
        assert type(getattr(report.market_family_summary_rows[0], name)) is Decimal


def test_event_resolution_acknowledgement_sla_late_postmortem_is_counted() -> None:
    report = _report(
        _row(
            "late-postmortem",
            event_resolved_at=GENERATED_AT - timedelta(seconds=7200),
            official_checked_at=GENERATED_AT - timedelta(seconds=300),
            resolution_acknowledged_at=GENERATED_AT - timedelta(seconds=6000),
            postmortem_acknowledged_at=GENERATED_AT - timedelta(seconds=3000),
        ),
    )

    assert report.report_status == "breached"
    assert report.exception_count == d("1.000000")
    assert report.sla_breach_count == d("1.000000")
    assert report.missing_postmortem_acknowledgement_count == d("0.000000")
    assert report.rows[0].postmortem_acknowledgement_age_seconds == d("4200.000000")
    assert report.rows[0].breach_seconds == d("600.000000")
    assert report.rows[0].reason_codes == (
        "market_event_resolution_acknowledgement_sla_breached",
        "market_event_resolution_postmortem_acknowledgement_late",
    )
    assert report.market_family_summary_rows[0].reason_codes == (
        "market_event_resolution_acknowledgement_sla_breached",
        "market_event_resolution_postmortem_acknowledgement_late",
    )


def test_event_resolution_acknowledgement_sla_module_is_pure_report_only_surface() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert ".total_seconds(" not in source
    assert "float(" not in source
    for banned in (
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ):
        assert banned not in source
        assert all(banned not in name.lower() for name in public_names)

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
                "read",
                "write",
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
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert "validate_market_event_resolution_acknowledgement_sla_public_payload" in public_names
