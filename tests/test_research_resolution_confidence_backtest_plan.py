from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


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
    return import_module(
        "polymarket_alpha_lab.research_resolution_confidence_backtest_plan",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values: dict[str, object] = {
        "config_version": "research-resolution-confidence-backtest-plan-v0",
        "min_closed_resolution_count": d("50.000000"),
        "min_confidence_bucket_count": d("5.000000"),
        "min_bucket_resolution_count": d("10.000000"),
        "max_confidence_error_watch": d("0.100000"),
        "max_confidence_error_block": d("0.200000"),
        "max_ambiguous_resolution_ratio_watch": d("0.100000"),
        "max_ambiguous_resolution_ratio_block": d("0.250000"),
        "max_missing_resolution_ratio_watch": d("0.050000"),
        "max_missing_resolution_ratio_block": d("0.150000"),
        "min_independent_review_count": d("2.000000"),
    }
    values.update(overrides)
    return api.ResearchResolutionConfidenceBacktestPlanConfig(**values)


def _plan_input(**overrides: object):
    api = _api()
    values: dict[str, object] = {
        "public_event_key": "event-family-001",
        "event_family": "macro-policy",
        "closed_resolution_count": d("80.000000"),
        "resolved_label_count": d("78.000000"),
        "ambiguous_resolution_count": d("1.000000"),
        "missing_resolution_count": d("1.000000"),
        "confidence_bucket_count": d("6.000000"),
        "smallest_bucket_resolution_count": d("12.000000"),
        "mean_absolute_confidence_error": d("0.050000"),
        "independent_review_count": d("3.000000"),
        "manual_review_required": False,
    }
    values.update(overrides)
    return api.ResearchResolutionConfidenceBacktestPlanInput(**values)


def _report(plan_input: object | None = None, *, cfg=None, generated_at=GENERATED_AT):
    api = _api()
    return api.build_research_resolution_confidence_backtest_plan(
        plan_input or _plan_input(),
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_pass_plan_builds_deterministic_public_queue_and_digest() -> None:
    api = _api()
    report = _report(
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    payload = api.research_resolution_confidence_backtest_plan_payload(report)
    payload_again = api.research_resolution_confidence_backtest_plan_payload(_report())

    assert type(report) is api.ResearchResolutionConfidenceBacktestPlanReport
    assert report.generated_at == GENERATED_AT
    assert report.area_count == d("5.000000")
    assert report.pass_count == d("5.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.status == "pass"
    assert report.reason_codes == ("resolution_confidence_backtest_plan_pass",)
    assert tuple(row.status for row in report.human_research_queue) == (
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
    )
    assert tuple(row.area for row in report.human_research_queue) == (
        "historical_resolution_samples",
        "resolution_label_completeness",
        "confidence_bucket_coverage",
        "confidence_error_review",
        "human_research_queue",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["area_count"] == "5.000000"
    assert payload["human_research_queue"][0]["observed_value"] == "80.000000"
    assert payload["human_research_queue"][0]["queue_priority"] == "0.000000"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload == payload_again
    assert json.dumps(payload, sort_keys=True) == json.dumps(payload_again, sort_keys=True)
    _assert_no_floats(payload)
    _assert_no_public_leaks(payload)


def test_watch_plan_flags_research_queue_without_blocking() -> None:
    report = _report(
        _plan_input(
            closed_resolution_count=d("40.000000"),
            resolved_label_count=d("36.000000"),
            ambiguous_resolution_count=d("3.000000"),
            missing_resolution_count=d("1.000000"),
            confidence_bucket_count=d("4.000000"),
            smallest_bucket_resolution_count=d("8.000000"),
            mean_absolute_confidence_error=d("0.150000"),
            independent_review_count=d("2.000000"),
            manual_review_required=True,
        ),
    )

    assert report.status == "watch"
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("4.000000")
    assert report.block_count == d("0.000000")
    assert report.reason_codes == ("watch_resolution_confidence_backtest_area",)
    assert tuple((row.area, row.status) for row in report.human_research_queue) == (
        ("historical_resolution_samples", "watch"),
        ("resolution_label_completeness", "pass"),
        ("confidence_bucket_coverage", "watch"),
        ("confidence_error_review", "watch"),
        ("human_research_queue", "watch"),
    )
    assert report.human_research_queue[0].gap_ratio == d("0.200000")
    assert report.human_research_queue[2].reason_codes == (
        "confidence_bucket_count_watch",
        "bucket_resolution_count_watch",
    )
    assert report.human_research_queue[4].reason_codes == ("manual_review_required",)


def test_block_plan_flags_insufficient_resolution_confidence_evidence() -> None:
    report = _report(
        _plan_input(
            closed_resolution_count=d("20.000000"),
            resolved_label_count=d("0.000000"),
            ambiguous_resolution_count=d("5.000000"),
            missing_resolution_count=d("3.000000"),
            confidence_bucket_count=d("0.000000"),
            smallest_bucket_resolution_count=d("0.000000"),
            mean_absolute_confidence_error=d("0.250000"),
            independent_review_count=d("0.000000"),
            manual_review_required=True,
        ),
    )

    assert report.status == "block"
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("4.000000")
    assert report.reason_codes == (
        "blocked_resolution_confidence_backtest_area",
        "watch_resolution_confidence_backtest_area",
    )
    assert tuple(row.status for row in report.human_research_queue) == (
        "watch",
        "block",
        "block",
        "block",
        "block",
    )
    assert report.human_research_queue[1].reason_codes == (
        "resolved_label_count_block",
        "missing_resolution_ratio_block",
        "ambiguous_resolution_ratio_block",
    )
    assert report.human_research_queue[3].reason_codes == ("confidence_error_block",)
    assert report.human_research_queue[4].queue_priority == d("1.000000")


def test_decimal_type_utc_bool_and_flag_rejections() -> None:
    api = _api()

    with pytest.raises(ValueError, match="Decimal"):
        _config(min_closed_resolution_count=50)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        _config(min_closed_resolution_count=_DecimalSubclass("50.000000"))
    with pytest.raises(ValueError, match="max_confidence_error_block"):
        _config(
            max_confidence_error_watch=d("0.200000"),
            max_confidence_error_block=d("0.200000"),
        )
    with pytest.raises(ValueError, match="closed_resolution_count"):
        _plan_input(closed_resolution_count=80)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="mean_absolute_confidence_error"):
        _plan_input(mean_absolute_confidence_error=d("1.100000"))
    with pytest.raises(ValueError, match="manual_review_required"):
        _plan_input(manual_review_required=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="label counts"):
        _plan_input(
            closed_resolution_count=d("1.000000"),
            resolved_label_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _report(generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="UTC offset"):
        _report(generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at"):
        _report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="config"):
        api.build_research_resolution_confidence_backtest_plan(
            _plan_input(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)


def test_public_leak_rejection_blocks_private_identifiers_and_action_language() -> None:
    api = _api()
    report = _report()

    for value in (
        "raw-candidate-123",
        "market-abc",
        "event-slug",
        "question-will-this-resolve",
        "source-ref-7",
        "https-url-token",
        "wallet-order-trade",
        "buy-sell-position",
        "recommend-yes",
    ):
        with pytest.raises(ValueError, match="unsafe public value"):
            _plan_input(public_event_key=value)

    unsafe_row = _bypassed(
        report.human_research_queue[0],
        reason_codes=("buy_yes_contracts",),
    )
    unsafe_report = _bypassed(
        report,
        human_research_queue=(unsafe_row, *report.human_research_queue[1:]),
    )
    object.__setattr__(
        unsafe_report,
        "derived_validation_digest",
        api._derived_validation_digest(unsafe_report),
    )
    with pytest.raises(ValueError, match="unsafe public value"):
        api.research_resolution_confidence_backtest_plan_payload(unsafe_report)


def test_report_digest_and_manual_consistency_validation() -> None:
    api = _api()
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.human_research_queue[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("4.000000"))
    with pytest.raises(ValueError, match="human_research_queue"):
        replace(report, human_research_queue=tuple(reversed(report.human_research_queue)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    stale_digest_report = _bypassed(report, status="watch")
    with pytest.raises(ValueError, match="status"):
        api.research_resolution_confidence_backtest_plan_payload(stale_digest_report)


def test_module_scope_is_report_only_without_network_write_or_execution_surface() -> None:
    module = _api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

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
        "json",
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
        "write_text",
    }.isdisjoint(called_names)

    report = _report()
    field_names = {field.name for field in fields(report)}
    row_field_names = {field.name for field in fields(report.human_research_queue[0])}
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
    ):
        assert all(forbidden not in name for name in field_names | row_field_names)


def _bypassed(value: object, **overrides: Any) -> object:
    malformed = object.__new__(type(value))
    for key, item in value.__dict__.items():
        object.__setattr__(malformed, key, item)
    for key, item in overrides.items():
        object.__setattr__(malformed, key, item)
    return malformed


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _assert_no_floats(item)


def _assert_no_public_leaks(value: object) -> None:
    forbidden = (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "ref",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            assert all(fragment not in key.lower() for fragment in forbidden)
            _assert_no_public_leaks(item)
    elif isinstance(value, str):
        assert all(fragment not in value.lower() for fragment in forbidden)
    elif isinstance(value, list | tuple):
        for item in value:
            _assert_no_public_leaks(item)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None
