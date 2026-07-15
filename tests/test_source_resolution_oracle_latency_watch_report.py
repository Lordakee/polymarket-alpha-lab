from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.source_resolution_oracle_latency_watch_report"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(
    *,
    oracle_source_present: bool = True,
    oracle_update_age_hours: Decimal = d("2.000000"),
    expected_resolution_hours: Decimal = d("24.000000"),
    dependency_count: Decimal = d("0.000000"),
    latency_threshold_hours: Decimal = d("6.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.build_source_resolution_oracle_latency_watch_report(
        oracle_source_present=oracle_source_present,
        oracle_update_age_hours=oracle_update_age_hours,
        expected_resolution_hours=expected_resolution_hours,
        dependency_count=dependency_count,
        latency_threshold_hours=latency_threshold_hours,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def assert_no_numeric_payload_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload_objects(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_numeric_payload_objects(item)
        return
    assert type(value) not in (Decimal, int, float)


def test_builds_pass_oracle_latency_report_payload_and_digest() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.SourceResolutionOracleLatencyWatchReport
    assert is_dataclass(report)
    assert report.oracle_latency_status == "pass"
    assert report.reason_codes == ("resolution_oracle_latency_within_threshold",)
    assert report.manual_next_step == "continue_resolution_oracle_monitoring"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == module.source_resolution_oracle_latency_watch_report_to_public_payload(
        report,
    )
    assert payload["oracle_source_present"] is True
    assert payload["oracle_update_age_hours"] == "2.000000"
    assert payload["expected_resolution_hours"] == "24.000000"
    assert payload["dependency_count"] == "0.000000"
    assert payload["latency_threshold_hours"] == "6.000000"
    assert payload["oracle_latency_status"] == "pass"
    assert payload["reason_codes"] == [
        "resolution_oracle_latency_within_threshold",
    ]
    assert payload["manual_next_step"] == "continue_resolution_oracle_monitoring"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.payload_digest) == 64
    int(report.payload_digest, 16)
    assert payload["payload_digest"] == report.payload_digest
    assert (
        module.source_resolution_oracle_latency_watch_report_digest(report)
        == report.payload_digest
    )
    assert module.validate_source_resolution_oracle_latency_watch_report_payload(payload)
    assert_no_numeric_payload_objects(payload)
    json.dumps(payload, sort_keys=True)


def test_status_reason_codes_and_manual_steps_are_deterministic() -> None:
    overdue = build_report(
        oracle_update_age_hours=d("7.000000"),
        expected_resolution_hours=d("24.000000"),
        dependency_count=d("0.000000"),
        latency_threshold_hours=d("6.000000"),
    )
    assert overdue.oracle_latency_status == "watch"
    assert overdue.reason_codes == ("oracle_update_age_exceeds_threshold",)
    assert overdue.manual_next_step == "manually_recheck_resolution_oracle"

    nearing_resolution = build_report(
        oracle_update_age_hours=d("4.000000"),
        expected_resolution_hours=d("3.000000"),
        dependency_count=d("0.000000"),
        latency_threshold_hours=d("6.000000"),
    )
    assert nearing_resolution.oracle_latency_status == "watch"
    assert nearing_resolution.reason_codes == ("expected_resolution_window_compressed",)
    assert nearing_resolution.manual_next_step == "manually_recheck_resolution_oracle"

    blocked = build_report(
        oracle_source_present=False,
        oracle_update_age_hours=d("14.000000"),
        expected_resolution_hours=d("2.000000"),
        dependency_count=d("3.000000"),
        latency_threshold_hours=d("6.000000"),
    )
    assert blocked.oracle_latency_status == "block"
    assert blocked.reason_codes == (
        "resolution_oracle_source_missing",
        "oracle_update_age_severely_exceeds_threshold",
        "expected_resolution_window_compressed",
        "resolution_dependency_chain_present",
    )
    assert blocked.manual_next_step == "pause_for_manual_resolution_oracle_review"


def test_payload_validation_rejects_tampering_numeric_objects_and_bad_flags() -> None:
    module = api()
    report = build_report(
        oracle_source_present=False,
        oracle_update_age_hours=d("14.000000"),
        expected_resolution_hours=d("2.000000"),
        dependency_count=d("3.000000"),
        latency_threshold_hours=d("6.000000"),
    )
    payload = report.public_payload

    tampered_payload = dict(payload)
    tampered_payload["oracle_latency_status"] = "pass"
    with pytest.raises(ValueError, match="payload_digest"):
        module.validate_source_resolution_oracle_latency_watch_report_payload(
            tampered_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["oracle_update_age_hours"] = 14
    with pytest.raises(ValueError, match="public payload"):
        module.validate_source_resolution_oracle_latency_watch_report_payload(
            numeric_payload,
        )

    flag_payload = dict(payload)
    flag_payload["report_only"] = False
    with pytest.raises(ValueError, match="payload report_only must be True"):
        module.validate_source_resolution_oracle_latency_watch_report_payload(
            flag_payload,
        )


def test_public_dataclass_is_frozen_decimal_only_and_rejects_unsafe_flags() -> None:
    module = api()
    assert module.__all__ == (
        "SourceResolutionOracleLatencyWatchReport",
        "build_source_resolution_oracle_latency_watch_report",
        "source_resolution_oracle_latency_watch_report_digest",
        "source_resolution_oracle_latency_watch_report_to_public_payload",
        "validate_source_resolution_oracle_latency_watch_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.oracle_latency_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.SourceResolutionOracleLatencyWatchReport):
            pass

    with pytest.raises(ValueError, match="oracle_update_age_hours"):
        build_report(oracle_update_age_hours=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="dependency_count"):
        build_report(dependency_count=d("1.500000"))
    with pytest.raises(ValueError, match="latency_threshold_hours"):
        build_report(latency_threshold_hours=d("0.000000"))
    with pytest.raises(ValueError, match="oracle_source_present"):
        build_report(oracle_source_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        build_report(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        build_report(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(readonly=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)

    for field in fields(report):
        value = getattr(report, field.name)
        assert type(value) is not float
        if field.name.endswith("_hours") or field.name == "dependency_count":
            assert type(value) is Decimal


def test_module_has_no_network_persistence_or_forbidden_path_surfaces() -> None:
    module = api()
    source = inspect.getsource(module).lower()
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "subprocess",
        "path(",
        "open(",
        ".write(",
        ".read(",
        "jsonl",
        "auth",
        "wallet",
        "keys",
        "signing",
        "execution",
        "crawl",
        "scrape",
        "live",
    ):
        assert forbidden not in source

    payload = build_report().public_payload
    material = {key: value for key, value in payload.items() if key != "payload_digest"}
    expected_digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert payload["payload_digest"] == expected_digest
