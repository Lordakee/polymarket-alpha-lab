from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
RECENT_AT = datetime(2026, 7, 2, 11, 50, tzinfo=UTC)
STALE_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _api():
    return import_module("polymarket_alpha_lab.research_market_rule_change_watch_report")


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values = {
        "config_version": "research-market-rule-change-watch-report-v0",
        "watch_change_count_threshold": d("1"),
        "block_change_count_threshold": d("2"),
        "watch_change_severity_threshold": d("0.250000"),
        "block_change_severity_threshold": d("0.750000"),
        "max_unreviewed_change_age_seconds": d("86400"),
    }
    values.update(overrides)
    return api.ResearchMarketRuleChangeWatchConfig(**values)


def _candidate(
    market_key: str = "market-alpha",
    *,
    prediction_rule_change_count: Decimal = d("1"),
    settlement_description_change_count: Decimal = d("0"),
    dependency_reference_change_count: Decimal = d("0"),
    prediction_rule_change_severity: Decimal = d("0.300000"),
    settlement_description_change_severity: Decimal = d("0.000000"),
    dependency_reference_change_severity: Decimal = d("0.000000"),
    latest_change_observed_at: datetime = RECENT_AT,
    change_review_acknowledged: bool = True,
):
    api = _api()
    return api.ResearchMarketRuleChangeWatchInput(
        market_key=market_key,
        prediction_rule_change_count=prediction_rule_change_count,
        settlement_description_change_count=settlement_description_change_count,
        dependency_reference_change_count=dependency_reference_change_count,
        prediction_rule_change_severity=prediction_rule_change_severity,
        settlement_description_change_severity=settlement_description_change_severity,
        dependency_reference_change_severity=dependency_reference_change_severity,
        latest_change_observed_at=latest_change_observed_at,
        change_review_acknowledged=change_review_acknowledged,
    )


def _report(rows: tuple[object, ...], *, cfg=None, generated_at: datetime = GENERATED_AT):
    api = _api()
    return api.build_research_market_rule_change_watch_report(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_rule_change_watch_report_classifies_pass_watch_and_block_rows():
    api = _api()
    report = _report(
        (
            _candidate(
                "market-block",
                prediction_rule_change_count=d("2"),
                settlement_description_change_count=d("1"),
                dependency_reference_change_count=d("1"),
                prediction_rule_change_severity=d("0.800000"),
                settlement_description_change_severity=d("0.300000"),
                dependency_reference_change_severity=d("0.300000"),
                latest_change_observed_at=STALE_AT,
                change_review_acknowledged=False,
            ),
            _candidate(
                "market-watch",
                prediction_rule_change_count=d("0"),
                settlement_description_change_count=d("0"),
                dependency_reference_change_count=d("1"),
                prediction_rule_change_severity=d("0.000000"),
                settlement_description_change_severity=d("0.000000"),
                dependency_reference_change_severity=d("0.300000"),
                latest_change_observed_at=GENERATED_AT - timedelta(minutes=10),
                change_review_acknowledged=True,
            ),
            _candidate(
                "market-pass",
                prediction_rule_change_count=d("0"),
                settlement_description_change_count=d("0"),
                dependency_reference_change_count=d("0"),
                prediction_rule_change_severity=d("0.000000"),
                settlement_description_change_severity=d("0.000000"),
                dependency_reference_change_severity=d("0.000000"),
                latest_change_observed_at=GENERATED_AT - timedelta(minutes=5),
                change_review_acknowledged=True,
            ),
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is api.ResearchMarketRuleChangeWatchReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-market-rule-change-watch-report-v0"
    assert report.observed_market_count == d("3")
    assert report.pass_market_count == d("1")
    assert report.watch_market_count == d("1")
    assert report.block_market_count == d("1")
    assert report.changed_market_count == d("2")
    assert report.unreviewed_change_count == d("1")
    assert report.max_change_count == d("2")
    assert report.max_change_severity == d("0.800000")
    assert report.max_change_age_seconds == d("86400")
    assert report.watch_ratio == d("0.666667")
    assert report.block_ratio == d("0.333333")
    assert report.status == "block"
    assert report.reason_codes == (
        "prediction_event_rule_change_present",
        "settlement_description_change_present",
        "dependency_reference_change_present",
        "missing_rule_change_review_present",
        "market_rule_change_block_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.change_rows
    assert block_row == api.ResearchMarketRuleChangeWatchRow(
        market_key="market-block",
        status="block",
        prediction_rule_change_count=d("2"),
        settlement_description_change_count=d("1"),
        dependency_reference_change_count=d("1"),
        max_change_count=d("2"),
        prediction_rule_change_severity=d("0.800000"),
        settlement_description_change_severity=d("0.300000"),
        dependency_reference_change_severity=d("0.300000"),
        max_change_severity=d("0.800000"),
        latest_change_age_seconds=d("86400"),
        flag_count=d("4"),
        prediction_event_rule_changed=True,
        settlement_description_changed=True,
        dependency_reference_changed=True,
        missing_rule_change_review=True,
        reason_codes=(
            "prediction_event_rule_changed",
            "settlement_description_changed",
            "dependency_reference_changed",
            "missing_rule_change_review",
        ),
        risk_notes=(
            "Prediction event rule changed; confirm event boundaries before use.",
            "Settlement description changed; confirm outcome criteria before use.",
            "Evidence dependency changed; confirm reference independence before use.",
            "Change review acknowledgement missing; keep the market in research watch.",
        ),
    )
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == ("dependency_reference_changed",)
    assert watch_row.risk_notes == (
        "Evidence dependency changed; confirm reference independence before use.",
    )
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("market_rule_change_clear",)
    assert pass_row.risk_notes == (
        "No review-triggering rule, settlement, or dependency change observed.",
    )


def test_empty_and_clear_reports_are_pass_decimal_report_only_and_json_ready():
    api = _api()
    empty = _report(())
    clear = _report(
        (
            _candidate(
                "market-clear",
                prediction_rule_change_count=d("0"),
                settlement_description_change_count=d("0"),
                dependency_reference_change_count=d("0"),
                prediction_rule_change_severity=d("0.000000"),
                settlement_description_change_severity=d("0.000000"),
                dependency_reference_change_severity=d("0.000000"),
                latest_change_observed_at=GENERATED_AT - timedelta(minutes=5),
                change_review_acknowledged=True,
            ),
        ),
    )

    assert empty.observed_market_count == d("0")
    assert empty.watch_ratio == d("0.000000")
    assert empty.block_ratio == d("0.000000")
    assert empty.status == "pass"
    assert empty.reason_codes == ("market_rule_change_watch_clear",)
    assert empty.change_rows == ()

    assert clear.observed_market_count == d("1")
    assert clear.pass_market_count == d("1")
    assert clear.changed_market_count == d("0")
    assert clear.status == "pass"
    assert clear.reason_codes == ("market_rule_change_watch_clear",)

    payload = api.research_market_rule_change_watch_payload(clear)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["observed_market_count"] == "1"
    assert payload["watch_ratio"] == "0.000000"
    assert payload["change_rows"][0]["status"] == "pass"
    assert payload["derived_validation_digest"] == clear.derived_validation_digest
    _assert_no_floats(payload)


def test_payload_exposes_stable_digest_and_rejects_sensitive_public_surfaces():
    api = _api()
    report = _report((_candidate(),))

    assert type(report.derived_validation_digest) is str
    assert len(report.derived_validation_digest) == 64
    assert int(report.derived_validation_digest, 16) >= 0
    assert _report((_candidate(),)).derived_validation_digest == report.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = api.research_market_rule_change_watch_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert type(payload["observed_market_count"]) is str
    assert type(payload["watch_ratio"]) is str
    assert type(payload["change_rows"][0]["max_change_severity"]) is str
    assert api.research_market_rule_change_watch_payload(payload) == payload

    with pytest.raises(ValueError, match="paper_only"):
        api.research_market_rule_change_watch_payload({**payload, "paper_only": False})
    with pytest.raises(ValueError, match="Decimal-derived"):
        api.research_market_rule_change_watch_payload(
            {**payload, "observed_market_count": 1},
        )
    with pytest.raises(ValueError, match="float"):
        api.research_market_rule_change_watch_payload(
            {**payload, "watch_ratio": 0.5},
        )

    for unsafe_key in (
        "raw_question",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "auth_token",
        "wallet_address",
        "order_id",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            api.research_market_rule_change_watch_payload(
                {**payload, unsafe_key: "redacted"},
            )

    for unsafe_value in (
        "will-this-market-settle",
        "https://example.invalid/reference",
        "postgres://example",
        "token=secret",
        "source text copied from a reference",
    ):
        bad_row = {**payload["change_rows"][0], "market_key": unsafe_value}
        with pytest.raises(ValueError, match="unsafe|redacted public identifier"):
            api.research_market_rule_change_watch_payload(
                {**payload, "change_rows": [bad_row]},
            )

    serialized = repr(payload).lower()
    for banned in ("raw_question", "market_slug", "source_url", "source_text", "dsn", "token"):
        assert banned not in serialized


def test_dataclasses_are_frozen_strict_decimal_utc_and_flag_guarded():
    api = _api()
    report = _report((_candidate(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.change_rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        _config(watch_change_severity_threshold=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="Decimal"):
        _candidate(prediction_rule_change_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        _candidate(prediction_rule_change_severity=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        _candidate(latest_change_observed_at=datetime(2026, 7, 2, 11, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        _report((), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="UTC offset"):
        _candidate(
            latest_change_observed_at=datetime(
                2026,
                7,
                2,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="UTC offset"):
        _report(
            (),
            generated_at=datetime(
                2026,
                7,
                2,
                12,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report((), generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="change_review_acknowledged"):
        _candidate(change_review_acknowledged=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="config"):
        api.build_research_market_rule_change_watch_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_rejects_duplicates_future_inputs_and_inconsistent_derived_values():
    report = _report(
        (
            _candidate("market-alpha"),
            _candidate(
                "market-beta",
                prediction_rule_change_count=d("0"),
                settlement_description_change_count=d("0"),
                dependency_reference_change_count=d("1"),
                prediction_rule_change_severity=d("0.000000"),
                settlement_description_change_severity=d("0.000000"),
                dependency_reference_change_severity=d("0.300000"),
                change_review_acknowledged=True,
            ),
        ),
    )

    with pytest.raises(ValueError, match="duplicate market_key"):
        _report((_candidate("market-dup"), _candidate("market-dup")))
    with pytest.raises(ValueError, match="latest_change_observed_at must not be after"):
        _report(
            (
                _candidate(
                    "market-future",
                    latest_change_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="must be zero"):
        _candidate(
            prediction_rule_change_count=d("0"),
            prediction_rule_change_severity=d("0.100000"),
        )
    with pytest.raises(ValueError, match="block_change_count_threshold"):
        _config(block_change_count_threshold=d("0"))
    with pytest.raises(ValueError, match="changed_market_count"):
        replace(report, changed_market_count=d("99"))
    with pytest.raises(ValueError, match="change_rows"):
        replace(report, change_rows=tuple(reversed(report.change_rows)))
    with pytest.raises(ValueError, match="flag_count"):
        replace(report.change_rows[0], flag_count=d("3"))


def test_module_scope_is_pure_in_memory_report_only_without_sensitive_surfaces():
    module = _api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert {
        "question",
        "slug",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "http://",
        "https://",
    }.issubset(set(module.UNSAFE_PUBLIC_SURFACE_FRAGMENTS))

    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                called_names.add(call_name.rsplit(".", maxsplit=1)[-1])

    assert imported_modules == {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
        "polymarket_alpha_lab.team_paper_guard",
    }
    assert {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "open",
        "print",
        "read_text",
        "request",
        "send",
        "socket",
        "trade",
        "write_text",
    }.isdisjoint(called_names)

    sample_report = _report((_candidate(),))
    report_field_names = {field.name for field in fields(sample_report)}
    row_field_names = {field.name for field in fields(sample_report.change_rows[0])}
    assert {
        "question",
        "market_slug",
        "source_url",
        "source_text",
        "raw_payload",
        "dsn",
        "table",
        "token",
        "private_key",
    }.isdisjoint(report_field_names | row_field_names)

    for field_name in (
        "observed_market_count",
        "pass_market_count",
        "watch_market_count",
        "block_market_count",
        "changed_market_count",
        "unreviewed_change_count",
        "max_change_count",
        "max_change_severity",
        "max_change_age_seconds",
        "watch_ratio",
        "block_ratio",
    ):
        assert type(getattr(sample_report, field_name)) is Decimal
    for field_name in (
        "prediction_rule_change_count",
        "settlement_description_change_count",
        "dependency_reference_change_count",
        "max_change_count",
        "prediction_rule_change_severity",
        "settlement_description_change_severity",
        "dependency_reference_change_severity",
        "max_change_severity",
        "latest_change_age_seconds",
        "flag_count",
    ):
        assert type(getattr(sample_report.change_rows[0], field_name)) is Decimal


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("JSON-ready values must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _assert_no_floats(item)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None
