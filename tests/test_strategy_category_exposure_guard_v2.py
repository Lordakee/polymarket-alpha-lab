from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_category_exposure_guard_v2.py"
)


def _api():
    return import_module("polymarket_alpha_lab.strategy_category_exposure_guard_v2")


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    values = {
        "config_version": "strategy-category-exposure-guard-v2-test",
        "category_watch_ratio": d("0.350000"),
        "category_block_ratio": d("0.450000"),
        "team_watch_ratio": d("0.350000"),
        "team_block_ratio": d("0.450000"),
        "event_watch_ratio": d("0.350000"),
        "event_block_ratio": d("0.450000"),
        "liquidity_pool_watch_ratio": d("0.350000"),
        "liquidity_pool_block_ratio": d("0.450000"),
        "settlement_date_watch_ratio": d("0.350000"),
        "settlement_date_block_ratio": d("0.450000"),
    }
    values.update(overrides)
    return _api().StrategyCategoryExposureGuardV2Config(**values)


def _position(**overrides: object):
    values = {
        "position_id": "position-fed-alpha",
        "category_id": "macro-rates",
        "team_id": "rates-team",
        "event_id": "fed-2026-event",
        "liquidity_pool_id": "fed-main-pool",
        "settlement_date": date(2026, 11, 4),
        "exposure_notional": d("250.000000"),
        "probability": d("0.570000"),
    }
    values.update(overrides)
    return _api().StrategyCategoryExposureGuardV2Position(**values)


def _candidate(**overrides: object):
    values = {
        "candidate_id": "candidate-fed-risk",
        "market_slug": "fed-cuts-by-november",
        "outcome_name": "Yes",
        "category_id": "macro-rates",
        "team_id": "rates-team",
        "event_id": "fed-2026-event",
        "liquidity_pool_id": "fed-main-pool",
        "settlement_date": date(2026, 11, 4),
        "proposed_notional": d("200.000000"),
        "probability": d("0.580000"),
        "liquidity_depth_notional": d("500.000000"),
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return _api().StrategyCategoryExposureGuardV2Candidate(**values)


def _existing_positions() -> tuple[object, ...]:
    return (
        _position(),
        _position(position_id="position-fed-beta", exposure_notional=d("150.000000")),
        _position(
            position_id="position-tennis",
            category_id="sports-tennis",
            team_id="tennis-team",
            event_id="tennis-final-event",
            liquidity_pool_id="tennis-main-pool",
            settlement_date=date(2026, 8, 1),
            exposure_notional=d("600.000000"),
            probability=d("0.420000"),
        ),
    )


def _build(*candidates: object, cfg: object | None = None):
    return _api().build_strategy_category_exposure_guard_v2_report(
        _existing_positions(),
        candidates,
        config=cfg if cfg is not None else _config(),
        generated_at=GENERATED_AT,
    )


def _row(report: object, candidate_id: str) -> object:
    for row in report.rows:
        if row.candidate_id == candidate_id:
            return row
    raise AssertionError(f"missing row for {candidate_id}")


def _assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numeric_scalars(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_public_numeric_scalars(item)


def test_build_report_flags_all_guard_dimensions_for_candidate_groups() -> None:
    api = _api()

    report = _build(
        _candidate(),
        _candidate(
            candidate_id="candidate-weather-pass",
            market_slug="rain-in-boston-september",
            outcome_name="No",
            category_id="weather",
            team_id="weather-team",
            event_id="boston-rain-event",
            liquidity_pool_id="weather-main-pool",
            settlement_date=date(2026, 9, 1),
            proposed_notional=d("100.000000"),
            probability=d("0.250000"),
            liquidity_depth_notional=d("800.000000"),
        ),
    )

    assert type(report) is api.StrategyCategoryExposureGuardV2Report
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-category-exposure-guard-v2-test"
    assert report.candidate_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("1.000000")
    assert report.status == "blocked"
    assert report.reason_codes == (
        "category_concentration_blocked",
        "team_concentration_blocked",
        "correlated_event_exposure_blocked",
        "liquidity_overlap_blocked",
        "settlement_date_cluster_blocked",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    risky = _row(report, "candidate-fed-risk")
    assert risky.total_portfolio_notional_after_candidate == d("1200.000000")
    assert risky.category_exposure_ratio == d("0.500000")
    assert risky.team_exposure_ratio == d("0.500000")
    assert risky.event_exposure_ratio == d("0.500000")
    assert risky.liquidity_pool_exposure_ratio == d("0.500000")
    assert risky.settlement_date_exposure_ratio == d("0.500000")
    assert risky.status == "blocked"
    assert risky.reason_codes == (
        "candidate_screened",
        "category_concentration_blocked",
        "team_concentration_blocked",
        "correlated_event_exposure_blocked",
        "liquidity_overlap_blocked",
        "settlement_date_cluster_blocked",
    )

    passing = _row(report, "candidate-weather-pass")
    assert passing.total_portfolio_notional_after_candidate == d("1100.000000")
    assert passing.category_exposure_ratio == d("0.090909")
    assert passing.team_exposure_ratio == d("0.090909")
    assert passing.event_exposure_ratio == d("0.090909")
    assert passing.liquidity_pool_exposure_ratio == d("0.090909")
    assert passing.settlement_date_exposure_ratio == d("0.090909")
    assert passing.status == "pass"
    assert passing.reason_codes == ("candidate_screened", "category_exposure_guard_v2_pass")


def test_watch_status_is_distinct_from_blocked_status() -> None:
    report = _build(
        _candidate(
            candidate_id="candidate-fed-watch",
            proposed_notional=d("50.000000"),
            liquidity_depth_notional=d("500.000000"),
        ),
    )

    row = report.rows[0]
    assert row.total_portfolio_notional_after_candidate == d("1050.000000")
    assert row.category_exposure_ratio == d("0.428571")
    assert row.status == "watch"
    assert report.status == "watch"
    assert "category_concentration_watch" in row.reason_codes
    assert "category_concentration_watch" in report.reason_codes


def test_dataclasses_are_frozen_exact_decimal_and_hard_flagged() -> None:
    api = _api()
    cfg = _config()
    position = _position()
    candidate = _candidate()
    report = _build(
        candidate,
        _candidate(
            candidate_id="candidate-weather-pass",
            market_slug="rain-in-boston-september",
            outcome_name="No",
            category_id="weather",
            team_id="weather-team",
            event_id="boston-rain-event",
            liquidity_pool_id="weather-main-pool",
            settlement_date=date(2026, 9, 1),
            proposed_notional=d("100.000000"),
            probability=d("0.250000"),
            liquidity_depth_notional=d("800.000000"),
        ),
        cfg=cfg,
    )
    row = _row(report, "candidate-fed-risk")

    for item in (cfg, position, candidate, row, report):
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert getattr(item, field.name) is True

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="proposed_notional must be a Decimal"):
        replace(candidate, proposed_notional=100)
    with pytest.raises(ValueError, match="probability must be a Decimal"):
        replace(candidate, probability=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="category watch threshold"):
        _config(category_watch_ratio=d("0.500000"), category_block_ratio=d("0.450000"))
    with pytest.raises(ValueError, match="rows must be deterministic"):
        replace(report, rows=tuple(reversed(report.rows)))


def test_payload_uses_decimal_strings_and_rejects_tampering() -> None:
    api = _api()
    report = _build(_candidate())

    payload = api.strategy_category_exposure_guard_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["proposed_notional"] == "200.000000"
    assert payload["rows"][0]["category_exposure_ratio"] == "0.500000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    _assert_no_public_numeric_scalars(payload)

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.strategy_category_exposure_guard_v2_payload(missing_digest)

    tampered = {
        **payload,
        "rows": [
            {
                **payload["rows"][0],
                "category_exposure_ratio": "0.499999",
            },
        ],
    }
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.strategy_category_exposure_guard_v2_payload(tampered)

    with pytest.raises(ValueError, match="Decimal-derived string"):
        api.strategy_category_exposure_guard_v2_payload({**payload, "candidate_count": 1})


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    api = _api()
    payload = api.strategy_category_exposure_guard_v2_payload(_build(_candidate()))

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{term}_surface"] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            api.strategy_category_exposure_guard_v2_payload(unsafe_key_payload)

        unsafe_value_payload = {
            **payload,
            "rows": [
                {
                    **payload["rows"][0],
                    "outcome_name": f"{term} surface configured",
                },
            ],
        }
        with pytest.raises(ValueError, match="unsafe"):
            api.strategy_category_exposure_guard_v2_payload(unsafe_value_payload)


def test_module_is_pure_readonly_decimal_only_and_unwired() -> None:
    api = _api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_calls = {
        "open",
        "read",
        "write",
        "connect",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "place_order",
        "submit_order",
        "execute",
    }
    forbidden_public_fragments = (
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] not in forbidden_import_roots for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_calls

    assert api.__all__ == (
        "StrategyCategoryExposureGuardV2Candidate",
        "StrategyCategoryExposureGuardV2Config",
        "StrategyCategoryExposureGuardV2Position",
        "StrategyCategoryExposureGuardV2Report",
        "StrategyCategoryExposureGuardV2Row",
        "build_strategy_category_exposure_guard_v2_report",
        "strategy_category_exposure_guard_v2_payload",
    )
    assert all(
        fragment not in public_name.lower()
        for public_name in api.__all__
        for fragment in forbidden_public_fragments
    )
