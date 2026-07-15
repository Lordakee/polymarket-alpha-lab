from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.source_time_series_evidence_gap_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "source_time_series_evidence_gap_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> Any:
    module = api()
    values = {
        "expected_observation_count": d("24.000000"),
        "captured_observation_count": d("24.000000"),
        "missing_interval_count": d("0.000000"),
        "latest_observation_age_hours": d("0.500000"),
        "official_series_present": True,
    }
    values.update(overrides)
    return module.build_source_time_series_evidence_gap_report(**values)


def assert_no_public_numeric(value: object) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, int, float)):
        raise AssertionError(f"unexpected public numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)


def test_clear_time_series_report_is_readonly_digest_bound_and_public() -> None:
    module = api()

    result = report()

    assert type(result) is module.SourceTimeSeriesEvidenceGapReport
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen is True
    assert result.expected_observation_count == d("24.000000")
    assert result.captured_observation_count == d("24.000000")
    assert result.missing_interval_count == d("0.000000")
    assert result.latest_observation_age_hours == d("0.500000")
    assert result.official_series_present is True
    assert result.evidence_gap_status == "clear"
    assert result.reason_codes == ("source_time_series_evidence_gap_clear",)
    assert result.manual_next_step == "continue_report_only_time_series_monitoring"
    assert len(result.payload_digest) == 64
    assert all(character in "0123456789abcdef" for character in result.payload_digest)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.public_payload
    assert payload == module.source_time_series_evidence_gap_public_payload(result)
    assert payload["expected_observation_count"] == "24.000000"
    assert payload["captured_observation_count"] == "24.000000"
    assert payload["missing_interval_count"] == "0.000000"
    assert payload["latest_observation_age_hours"] == "0.500000"
    assert payload["official_series_present"] is True
    assert payload["evidence_gap_status"] == "clear"
    assert payload["reason_codes"] == ["source_time_series_evidence_gap_clear"]
    assert payload["manual_next_step"] == "continue_report_only_time_series_monitoring"
    assert payload["payload_digest"] == result.payload_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.validate_source_time_series_evidence_gap_public_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_missing_and_stale_time_series_evidence_is_blocked() -> None:
    result = report(
        expected_observation_count=d("24.000000"),
        captured_observation_count=d("20.000000"),
        missing_interval_count=d("4.000000"),
        latest_observation_age_hours=d("3.250000"),
        official_series_present=False,
    )

    assert result.evidence_gap_status == "blocked"
    assert result.reason_codes == (
        "official_time_series_missing",
        "time_series_capture_incomplete",
        "time_series_intervals_missing",
        "latest_time_series_observation_stale",
    )
    assert result.manual_next_step == "manual_source_time_series_backfill_required"

    payload = result.public_payload
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["payload_digest"] == result.payload_digest
    assert_no_public_numeric(payload)


def test_no_expected_observations_is_watch_not_blocked() -> None:
    result = report(
        expected_observation_count=d("0.000000"),
        captured_observation_count=d("0.000000"),
        missing_interval_count=d("0.000000"),
        latest_observation_age_hours=d("0.000000"),
        official_series_present=True,
    )

    assert result.evidence_gap_status == "watch"
    assert result.reason_codes == ("time_series_expected_observation_count_zero",)
    assert result.manual_next_step == "manual_confirm_time_series_expectation"


def test_dataclass_is_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    result = report()

    with pytest.raises(FrozenInstanceError):
        result.evidence_gap_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="expected_observation_count"):
        report(expected_observation_count=24)
    with pytest.raises(ValueError, match="captured_observation_count"):
        report(captured_observation_count=_DecimalSubclass("24.000000"))
    with pytest.raises(ValueError, match="latest_observation_age_hours"):
        report(latest_observation_age_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="official_series_present"):
        report(official_series_present=1)
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)


def test_payload_tampering_and_forbidden_source_surface_are_rejected() -> None:
    module = api()
    result = report()
    payload = dict(result.public_payload)
    payload["captured_observation_count"] = "23.000000"

    with pytest.raises(ValueError, match="payload_digest"):
        module.validate_source_time_series_evidence_gap_public_payload(payload)

    source_text = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    forbidden_terms = (
        "auth",
        "wallet",
        "key",
        "signature",
        "signing",
        "live",
        "crawler",
        "scrape",
        "network",
        "order",
        "trade",
        "execute",
        "jsonl",
        "open(",
        "requests",
        "urllib",
        "socket",
        "subprocess",
    )
    lowered_literals = " ".join(
        node.value.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )
    for term in forbidden_terms:
        assert term not in lowered_literals
