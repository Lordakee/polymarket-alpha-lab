from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "market-outcome-freshness-recheck-status-test-v0"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "market_outcome_freshness_recheck_status_report.py"
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_outcome_freshness_recheck_status_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "stale_source_after_seconds": d("1800"),
        "acknowledgement_lag_after_seconds": d("900"),
    }
    values.update(overrides)
    return module.MarketOutcomeFreshnessRecheckStatusConfig(**values)


def _recheck(
    recheck_id: str,
    *,
    market_id: str | None = None,
    outcome_id: str = "yes",
    team_id: str = "research",
    requested_at: datetime = datetime(2026, 7, 2, 11, 30, tzinfo=UTC),
    due_at: datetime = datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
    source_checked_at: datetime | None = datetime(2026, 7, 2, 11, 55, tzinfo=UTC),
    official_outcome: str | None = "yes",
    proxy_outcome: str | None = "yes",
    acknowledged_at: datetime | None = datetime(2026, 7, 2, 11, 35, tzinfo=UTC),
    cleared_at: datetime | None = None,
    blocked_at: datetime | None = None,
    blocked_reason_code: str | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    suffix = recheck_id.removeprefix("recheck-")
    return module.MarketOutcomeFreshnessRecheckStatusInput(
        recheck_id=recheck_id,
        market_id=market_id or f"market-{suffix}",
        outcome_id=outcome_id,
        team_id=team_id,
        requested_at=requested_at,
        due_at=due_at,
        source_checked_at=source_checked_at,
        official_outcome=official_outcome,
        proxy_outcome=proxy_outcome,
        acknowledged_at=acknowledged_at,
        cleared_at=cleared_at,
        blocked_at=blocked_at,
        blocked_reason_code=blocked_reason_code,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _build_report(*rechecks, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_outcome_freshness_recheck_status_report(
        rechecks,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def _field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def _assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain float values")
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_no_float_values(key)
            _assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_float_values(item)


def test_status_report_summarizes_recheck_states_deterministically() -> None:
    report = _build_report(
        _recheck(
            "recheck-clear",
            cleared_at=datetime(2026, 7, 2, 11, 50, tzinfo=UTC),
        ),
        _recheck(
            "recheck-overdue",
            requested_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
            due_at=datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
            source_checked_at=datetime(2026, 7, 2, 11, 50, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 10, 10, tzinfo=UTC),
        ),
        _recheck(
            "recheck-blocked",
            requested_at=datetime(2026, 7, 2, 9, 30, tzinfo=UTC),
            due_at=datetime(2026, 7, 2, 11, 30, tzinfo=UTC),
            source_checked_at=datetime(2026, 7, 2, 11, 45, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 9, 35, tzinfo=UTC),
            blocked_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
            blocked_reason_code="official_source_unavailable",
        ),
        _recheck(
            "recheck-stale-source",
            requested_at=datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
            source_checked_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 11, 5, tzinfo=UTC),
        ),
        _recheck(
            "recheck-proxy",
            requested_at=datetime(2026, 7, 2, 11, 15, tzinfo=UTC),
            source_checked_at=datetime(2026, 7, 2, 11, 45, tzinfo=UTC),
            official_outcome="yes",
            proxy_outcome="no",
            acknowledged_at=datetime(2026, 7, 2, 11, 20, tzinfo=UTC),
        ),
        _recheck(
            "recheck-ack-lag",
            requested_at=datetime(2026, 7, 2, 10, 30, tzinfo=UTC),
            source_checked_at=datetime(2026, 7, 2, 11, 50, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
        ),
    )

    assert report.status == "blocked"
    assert report.reason_codes == (
        "outcome_freshness_recheck_blocked",
        "outcome_freshness_recheck_proxy_contradiction",
        "outcome_freshness_recheck_overdue",
        "outcome_freshness_recheck_stale_source",
        "outcome_freshness_recheck_acknowledgement_lag",
    )
    assert report.recheck_count == d("6")
    assert report.blocked_count == d("2")
    assert report.overdue_count == d("1")
    assert report.watch_count == d("2")
    assert report.cleared_count == d("1")
    assert report.stale_source_count == d("1")
    assert report.proxy_contradiction_count == d("1")
    assert report.acknowledgement_lag_count == d("1")
    assert report.cleared_ratio == d("0.166667")
    assert report.max_recheck_age_seconds == d("9000.000000")
    assert report.max_overdue_age_seconds == d("3600.000000")
    assert report.max_source_age_seconds == d("10800.000000")
    assert report.max_acknowledgement_lag_seconds == d("1800.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.recheck_id for row in report.rows) == (
        "recheck-blocked",
        "recheck-proxy",
        "recheck-overdue",
        "recheck-stale-source",
        "recheck-ack-lag",
        "recheck-clear",
    )
    assert report.rows[0].status == "blocked"
    assert report.rows[0].reason_codes == ("outcome_freshness_recheck_blocked",)
    assert report.rows[1].status == "blocked"
    assert report.rows[1].reason_codes == (
        "outcome_freshness_recheck_proxy_contradiction",
    )
    assert report.rows[2].status == "overdue"
    assert report.rows[2].overdue_age_seconds == d("3600.000000")
    assert report.rows[3].status == "watch"
    assert report.rows[3].source_age_seconds == d("10800.000000")
    assert report.rows[4].status == "watch"
    assert report.rows[4].acknowledgement_lag_seconds == d("1800.000000")
    assert report.rows[5].status == "cleared"
    assert report.rows[5].reason_codes == ("outcome_freshness_recheck_cleared",)


def test_empty_report_is_decimal_report_only_and_json_ready() -> None:
    module = api()
    report = _build_report()

    assert report.status == "empty"
    assert report.reason_codes == ("outcome_freshness_recheck_empty",)
    assert report.recheck_count == d("0")
    assert report.blocked_count == d("0")
    assert report.overdue_count == d("0")
    assert report.watch_count == d("0")
    assert report.cleared_count == d("0")
    assert report.cleared_ratio == d("0.000000")
    assert report.max_recheck_age_seconds == d("0.000000")
    assert report.rows == ()

    payload = module.market_outcome_freshness_recheck_status_report_payload(report)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["recheck_count"] == "0"
    assert payload["cleared_ratio"] == "0.000000"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_datetimes_flags_uniqueness_and_decimal_public_fields_are_validated() -> None:
    module = api()
    local_generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    local_requested_at = datetime(2026, 7, 2, 7, 0, tzinfo=timezone(timedelta(hours=-4)))
    report = _build_report(
        _recheck(
            "recheck-timezone",
            requested_at=local_requested_at,
            due_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
            source_checked_at=datetime(2026, 7, 2, 11, 55, tzinfo=UTC),
        ),
        generated_at=local_generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].requested_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(_recheck("recheck-flag"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_config(), report_only=False)
    with pytest.raises(ValueError, match="stale_source_after_seconds"):
        replace(_config(), stale_source_after_seconds=d("1.1"))
    with pytest.raises(ValueError, match="acknowledgement_lag_after_seconds"):
        replace(_config(), acknowledgement_lag_after_seconds=900)
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_outcome_freshness_recheck_status_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="requested_at must be timezone-aware"):
        _recheck("recheck-naive", requested_at=datetime(2026, 7, 2, 11, 0))
    with pytest.raises(ValueError, match="requested_at must be <= generated_at"):
        _build_report(
            _recheck(
                "recheck-future",
                requested_at=GENERATED_AT + timedelta(seconds=1),
                due_at=GENERATED_AT + timedelta(minutes=1),
                acknowledged_at=GENERATED_AT + timedelta(seconds=2),
            ),
        )
    with pytest.raises(ValueError, match="recheck_id values must be unique"):
        _build_report(_recheck("recheck-dup"), _recheck("recheck-dup"))
    with pytest.raises(ValueError, match="blocked_reason_code is required"):
        _recheck(
            "recheck-blocked-no-reason",
            blocked_at=datetime(2026, 7, 2, 11, 45, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="cleared_at and blocked_at"):
        _recheck(
            "recheck-terminal-conflict",
            cleared_at=datetime(2026, 7, 2, 11, 40, tzinfo=UTC),
            blocked_at=datetime(2026, 7, 2, 11, 45, tzinfo=UTC),
            blocked_reason_code="manual_review",
        )
    with pytest.raises(ValueError, match="source_checked_at must be <= generated_at"):
        _build_report(
            _recheck(
                "recheck-source-future",
                source_checked_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    for instance in (_config(), _recheck("recheck-decimal"), report, report.rows[0]):
        for field in fields(instance):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_age_seconds")
                or field.name.endswith("_after_seconds")
            ):
                value = getattr(instance, field.name)
                assert value is None or type(value) is Decimal, (field.name, value)


def test_payload_helper_and_module_surface_are_report_only() -> None:
    module = api()
    report = _build_report(_recheck("recheck-json"))
    payload = module.market_outcome_freshness_recheck_status_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["recheck_count"] == "1"
    assert payload["cleared_ratio"] == "1.000000"
    assert payload["rows"][0]["recheck_age_seconds"] == "1800.000000"
    assert payload["rows"][0]["paper_only"] is True
    _assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)

    rebuilt_row = module.MarketOutcomeFreshnessRecheckStatusRow(
        **_field_values(report.rows[0]),
    )
    rebuilt_report = module.MarketOutcomeFreshnessRecheckStatusReport(
        **_field_values(report),
    )
    assert rebuilt_row == report.rows[0]
    assert rebuilt_report == report

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    assert _module_exports(tree) == (
        "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_STATUS_CONFIG_VERSION",
        "MarketOutcomeFreshnessRecheckStatusConfig",
        "MarketOutcomeFreshnessRecheckStatusInput",
        "MarketOutcomeFreshnessRecheckStatusReport",
        "MarketOutcomeFreshnessRecheckStatusRow",
        "build_market_outcome_freshness_recheck_status_report",
        "market_outcome_freshness_recheck_status_report_payload",
    )
    assert set(_imported_modules(tree)) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
    }
    normalized_names = {
        _normalize_identifier(name)
        for name in _collected_names(tree)
        if _normalize_identifier(name) != "readonly"
    }
    for fragment in (
        "persistence",
        "network",
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
    ):
        assert not any(fragment in name for name in normalized_names), fragment
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "__import__",
                "compile",
                "eval",
                "exec",
                "input",
                "open",
                "print",
                "read",
                "write",
            }


def _module_exports(tree: ast.Module) -> tuple[str, ...]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return tuple(ast.literal_eval(node.value))
    raise AssertionError("__all__ not found")


def _imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def _collected_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)
    return names


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())
