from __future__ import annotations

import dataclasses
import inspect
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.source_primary_reference_stability_report",
    )


def report(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "primary_reference_present": True,
        "reference_digest_changed": False,
        "official_update_count": d("0.000000"),
        "source_age_hours": d("2.000000"),
        "fallback_reference_count": d("0.000000"),
    }
    values.update(overrides)
    return module.build_source_primary_reference_stability_report(**values)


def assert_payload_has_no_numeric_values(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_numeric_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_numeric_values(item)


def test_clear_primary_reference_returns_stable_report_only_payload() -> None:
    module = api()

    result = report()

    assert result == module.SourcePrimaryReferenceStabilityReport(
        reference_stability_status="stable",
        reason_codes=("primary_reference_stable",),
        manual_next_step="continue_primary_reference_monitoring",
        primary_reference_present=True,
        reference_digest_changed=False,
        official_update_count=d("0.000000"),
        source_age_hours=d("2.000000"),
        fallback_reference_count=d("0.000000"),
        payload_digest=result.payload_digest,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    with pytest.raises(FrozenInstanceError):
        result.reference_stability_status = "watch"  # type: ignore[misc]

    payload = result.public_payload
    assert payload == module.source_primary_reference_stability_public_payload(result)
    assert payload["reference_stability_status"] == "stable"
    assert payload["manual_next_step"] == "continue_primary_reference_monitoring"
    assert payload["reason_codes"] == ["primary_reference_stable"]
    assert payload["official_update_count"] == "0.000000"
    assert payload["source_age_hours"] == "2.000000"
    assert payload["fallback_reference_count"] == "0.000000"
    assert payload["payload_digest"] == result.payload_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_payload_has_no_numeric_values(payload)
    assert module.validate_source_primary_reference_stability_payload_digest(payload)


def test_changed_digest_and_official_updates_block_for_manual_refresh() -> None:
    result = report(
        reference_digest_changed=True,
        official_update_count=d("2.000000"),
        source_age_hours=d("1.500000"),
        fallback_reference_count=d("1.000000"),
    )

    assert result.reference_stability_status == "blocked"
    assert result.reason_codes == (
        "reference_digest_changed",
        "official_updates_detected",
        "fallback_references_present",
        "primary_reference_stability_blocked",
    )
    assert result.manual_next_step == "manual_review_primary_reference_update"


def test_missing_or_stale_primary_reference_requires_watch_or_block() -> None:
    missing = report(primary_reference_present=False)
    stale = report(source_age_hours=d("30.000000"))
    fallback = report(fallback_reference_count=d("1.000000"))
    severe = report(
        primary_reference_present=False,
        source_age_hours=d("60.000000"),
        fallback_reference_count=d("3.000000"),
    )

    assert missing.reference_stability_status == "blocked"
    assert missing.reason_codes == (
        "primary_reference_missing",
        "primary_reference_stability_blocked",
    )
    assert missing.manual_next_step == "restore_primary_reference_before_use"
    assert stale.reference_stability_status == "watch"
    assert stale.reason_codes == (
        "primary_reference_stale",
        "primary_reference_stability_watch",
    )
    assert stale.manual_next_step == "manual_refresh_primary_reference"
    assert fallback.reference_stability_status == "watch"
    assert fallback.reason_codes == (
        "fallback_references_present",
        "primary_reference_stability_watch",
    )
    assert severe.reference_stability_status == "blocked"
    assert severe.manual_next_step == "restore_primary_reference_before_use"


def test_digest_is_deterministic_and_rejects_tampered_payloads() -> None:
    module = api()
    first = report(source_age_hours=d("30.000000"))
    second = report(source_age_hours=d("30.000000"))

    assert first.payload_digest == second.payload_digest
    assert first.public_payload == second.public_payload

    tampered = dict(first.public_payload)
    tampered["source_age_hours"] = "31.000000"
    assert not module.validate_source_primary_reference_stability_payload_digest(tampered)
    with pytest.raises(ValueError, match="payload_digest"):
        module.SourcePrimaryReferenceStabilityReport(
            reference_stability_status=first.reference_stability_status,
            reason_codes=first.reason_codes,
            manual_next_step=first.manual_next_step,
            primary_reference_present=first.primary_reference_present,
            reference_digest_changed=first.reference_digest_changed,
            official_update_count=first.official_update_count,
            source_age_hours=first.source_age_hours,
            fallback_reference_count=first.fallback_reference_count,
            payload_digest="0" * 64,
        )


def test_inputs_are_decimal_only_and_hard_flags_must_remain_true() -> None:
    module = api()

    with pytest.raises(ValueError, match="official_update_count must be a Decimal"):
        report(official_update_count=1)
    with pytest.raises(ValueError, match="source_age_hours must be a Decimal"):
        report(source_age_hours=1.0)
    with pytest.raises(ValueError, match="fallback_reference_count must be a Decimal"):
        report(fallback_reference_count="1.000000")
    with pytest.raises(ValueError, match="source_age_hours must be non-negative"):
        report(source_age_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="official_update_count must be an integer count"):
        report(official_update_count=d("1.500000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report(), paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(report(), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report(), readonly=False)

    for item in (report(),):
        assert dataclasses.is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
    with pytest.raises(TypeError):
        type("ChildReport", (module.SourcePrimaryReferenceStabilityReport,), {})


def test_module_is_pure_readonly_report_without_network_or_persistence_paths() -> None:
    module = api()
    source = inspect.getsource(module)
    lowered = source.lower()

    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "websocket",
        "psycopg",
        "supabase",
        "open(",
        ".write(",
        "jsonl",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "signature",
        "sign_order",
        "submit_order",
        "cancel_order",
        "live",
        "auth",
        "scrape",
    )
    assert not any(term in lowered for term in forbidden_terms)

    path = Path(module.__file__).resolve()
    assert path.name == "source_primary_reference_stability_report.py"
    assert "source_primary_reference_stability_report" in module.__all__
    json.dumps(report().public_payload, sort_keys=True)
