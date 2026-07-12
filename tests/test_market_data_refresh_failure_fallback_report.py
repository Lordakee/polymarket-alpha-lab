from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_data_refresh_failure_fallback_report"
SOURCE = Path("src/polymarket_alpha_lab/market_data_refresh_failure_fallback_report.py")


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> object:
    return importlib.import_module(MODULE_NAME)


def _report(**overrides: object) -> object:
    api = _api()
    values = {
        "primary_refresh_failed": True,
        "fallback_source_count": d("2.000000"),
        "last_success_age_hours": d("1.500000"),
        "market_move_probability": d("0.080000"),
        "manual_refresh_owner_present": True,
    }
    values.update(overrides)
    return api.build_market_data_refresh_failure_fallback_report(**values)


def test_failed_primary_refresh_with_sources_and_owner_is_manual_fallback_ready() -> None:
    report = _report()

    assert is_dataclass(report)
    assert report.fallback_status == "ready"
    assert report.reason_codes == (
        "primary_refresh_failed",
        "fallback_sources_available",
        "manual_owner_present",
    )
    assert report.manual_next_step == "prepare_manual_refresh_packet"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == {
        "primary_refresh_failed": True,
        "fallback_source_count": "2.000000",
        "last_success_age_hours": "1.500000",
        "market_move_probability": "0.080000",
        "manual_refresh_owner_present": True,
        "fallback_status": "ready",
        "reason_codes": [
            "primary_refresh_failed",
            "fallback_sources_available",
            "manual_owner_present",
        ],
        "manual_next_step": "prepare_manual_refresh_packet",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": report.payload_digest,
    }
    without_digest = dict(payload)
    without_digest.pop("payload_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            without_digest,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert report.payload_digest == expected_digest


def test_statuses_explain_not_needed_watch_and_blocked_fallback_paths() -> None:
    not_needed = _report(primary_refresh_failed=False)
    assert not_needed.fallback_status == "not_needed"
    assert not_needed.reason_codes == ("primary_refresh_available",)
    assert not_needed.manual_next_step == "no_manual_fallback_needed"

    watch = _report(
        fallback_source_count=d("1.000000"),
        last_success_age_hours=d("8.000000"),
        market_move_probability=d("0.140000"),
    )
    assert watch.fallback_status == "watch"
    assert watch.reason_codes == (
        "primary_refresh_failed",
        "single_fallback_source",
        "manual_owner_present",
        "last_success_stale",
        "market_move_watch",
    )
    assert watch.manual_next_step == "verify_single_fallback_source"

    blocked = _report(
        fallback_source_count=d("0.000000"),
        manual_refresh_owner_present=False,
    )
    assert blocked.fallback_status == "blocked"
    assert blocked.reason_codes == (
        "primary_refresh_failed",
        "fallback_sources_missing",
        "manual_owner_missing",
    )
    assert blocked.manual_next_step == "assign_manual_refresh_owner"


def test_report_is_frozen_exact_dataclass_and_rejects_unsafe_flags() -> None:
    api = _api()
    report = _report()

    assert type(report) is api.MarketDataRefreshFailureFallbackReport
    with pytest.raises(FrozenInstanceError):
        report.fallback_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):

        class SubReport(api.MarketDataRefreshFailureFallbackReport):  # type: ignore[misc,valid-type]
            pass

    for flag_name in ("paper_only", "report_only", "readonly"):
        kwargs = {
            "primary_refresh_failed": True,
            "fallback_source_count": d("2.000000"),
            "last_success_age_hours": d("1.500000"),
            "market_move_probability": d("0.080000"),
            "manual_refresh_owner_present": True,
            flag_name: False,
        }
        with pytest.raises(ValueError, match=flag_name):
            api.MarketDataRefreshFailureFallbackReport(**kwargs)


def test_decimal_only_inputs_and_payload_numeric_strings() -> None:
    api = _api()

    type_hints = {
        field.name: field.type
        for field in fields(api.MarketDataRefreshFailureFallbackReport)
    }
    assert type_hints["fallback_source_count"] == Decimal
    assert type_hints["last_success_age_hours"] == Decimal
    assert type_hints["market_move_probability"] == Decimal

    with pytest.raises(ValueError, match="fallback_source_count"):
        _report(fallback_source_count=2)
    with pytest.raises(ValueError, match="last_success_age_hours"):
        _report(last_success_age_hours=1.5)
    with pytest.raises(ValueError, match="market_move_probability"):
        _report(market_move_probability="0.1")

    payload = _report().public_payload
    for key in (
        "fallback_source_count",
        "last_success_age_hours",
        "market_move_probability",
    ):
        assert type(payload[key]) is str
        Decimal(payload[key])


def test_report_rejects_invalid_ranges_and_inconsistent_status_overrides() -> None:
    api = _api()

    with pytest.raises(ValueError, match="primary_refresh_failed"):
        _report(primary_refresh_failed="yes")
    with pytest.raises(ValueError, match="manual_refresh_owner_present"):
        _report(manual_refresh_owner_present=1)
    with pytest.raises(ValueError, match="fallback_source_count"):
        _report(fallback_source_count=d("-1.000000"))
    with pytest.raises(ValueError, match="last_success_age_hours"):
        _report(last_success_age_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="market_move_probability"):
        _report(market_move_probability=d("1.000001"))

    with pytest.raises(ValueError, match="fallback_status"):
        api.MarketDataRefreshFailureFallbackReport(
            primary_refresh_failed=True,
            fallback_source_count=d("2.000000"),
            last_success_age_hours=d("1.500000"),
            market_move_probability=d("0.080000"),
            manual_refresh_owner_present=True,
            fallback_status="blocked",
            reason_codes=("primary_refresh_failed",),
            manual_next_step="assign_manual_refresh_owner",
        )


def test_module_is_readonly_report_only_and_has_no_external_side_effect_surface() -> None:
    api = _api()
    source = SOURCE.read_text(encoding="utf-8").lower()

    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "jsonl",
        ".write(",
        "open(",
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "secret",
        "signature",
        "signing",
        "execute",
        "executing",
    )
    for term in forbidden_terms:
        assert term not in source

    public_names = set(api.__all__)
    assert public_names == {
        "MarketDataRefreshFailureFallbackReport",
        "build_market_data_refresh_failure_fallback_report",
    }
    for name in public_names:
        obj = getattr(api, name)
        assert inspect.getmodule(obj) is api
