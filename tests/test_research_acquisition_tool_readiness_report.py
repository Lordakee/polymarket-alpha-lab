from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_acquisition_tool_readiness_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.research_acquisition_tool_readiness_report",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"expected report module to exist: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> Any:
    module = api()
    values = {
        "official_api_available": True,
        "agent_reach_available": True,
        "scrapling_available": True,
        "last_success_age_seconds": d("600.000000"),
        "failed_attempt_count": d("0.000000"),
        "source_payload_redacted": True,
        "manual_fallback_required": False,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.build_research_acquisition_tool_readiness_report(**values)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _assert_payload_has_no_raw_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        pytest.fail(f"public payload leaked raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            _assert_payload_has_no_raw_numbers(item)
    elif type(value) is list:
        for item in value:
            _assert_payload_has_no_raw_numbers(item)


def _assert_payload_has_no_forbidden_text(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).casefold()
    for forbidden in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live_trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in rendered


def test_all_tools_available_with_fresh_redacted_payload_is_ready() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchAcquisitionToolReadinessReport
    assert is_dataclass(report)
    assert report.acquisition_tool_ready is True
    assert report.tool_quorum_ready is True
    assert report.available_tool_count == d("3.000000")
    assert report.blocked_tool_count == d("0.000000")
    assert report.attention_tool_count == d("0.000000")
    assert report.ready_ratio == d("1.000000")
    assert report.reason_codes == ("research_acquisition_tool_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == module.research_acquisition_tool_readiness_report_public_payload(report)
    assert payload["ready_ratio"] == "1.000000"
    assert payload["blocked_tool_count"] == "0.000000"
    assert payload["digest"] == report.digest
    assert payload["digest"] == canonical_digest(payload)
    assert module.validate_research_acquisition_tool_readiness_report_public_payload(
        payload,
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_text(payload)


def test_quorum_can_pass_while_manual_fallback_keeps_acquisition_blocked() -> None:
    report = build_report(
        scrapling_available=False,
        last_success_age_seconds=d("90000.000000"),
        failed_attempt_count=d("1.000000"),
        manual_fallback_required=True,
    )

    assert report.acquisition_tool_ready is False
    assert report.tool_quorum_ready is True
    assert report.available_tool_count == d("2.000000")
    assert report.blocked_tool_count == d("1.000000")
    assert report.attention_tool_count == d("3.000000")
    assert report.ready_ratio == d("0.666667")
    assert report.reason_codes == (
        "scrapling_unavailable",
        "last_success_age_watch",
        "failed_attempts_present",
        "manual_fallback_required",
    )


def test_missing_quorum_and_unredacted_payload_block_readiness() -> None:
    report = build_report(
        official_api_available=False,
        agent_reach_available=False,
        scrapling_available=True,
        last_success_age_seconds=d("300000.000000"),
        failed_attempt_count=d("3.000000"),
        source_payload_redacted=False,
    )

    assert report.acquisition_tool_ready is False
    assert report.tool_quorum_ready is False
    assert report.available_tool_count == d("1.000000")
    assert report.blocked_tool_count == d("2.000000")
    assert report.attention_tool_count == d("4.000000")
    assert report.ready_ratio == d("0.333333")
    assert report.reason_codes == (
        "official_api_unavailable",
        "agent_reach_unavailable",
        "tool_quorum_missing",
        "last_success_age_block",
        "failed_attempts_elevated",
        "source_payload_not_redacted",
    )


def test_decimal_only_frozen_exact_types_flags_and_payload_validation() -> None:
    module = api()
    report = build_report()

    assert module.ResearchAcquisitionToolReadinessReport.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        report.ready_ratio = d("0.000000")  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "DerivedResearchAcquisitionToolReadinessReport",
            (module.ResearchAcquisitionToolReadinessReport,),
            {},
        )

    for bad_kwargs, match in (
        ({"last_success_age_seconds": 600}, "last_success_age_seconds"),
        ({"failed_attempt_count": 0}, "failed_attempt_count"),
        ({"last_success_age_seconds": _DecimalSubclass("1.000000")}, "last_success_age_seconds"),
        ({"failed_attempt_count": d("-1.000000")}, "failed_attempt_count"),
        ({"official_api_available": 1}, "official_api_available"),
        ({"manual_fallback_required": 0}, "manual_fallback_required"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ):
        with pytest.raises(ValueError, match=match):
            build_report(**bad_kwargs)

    with pytest.raises(ValueError, match="digest"):
        replace(report, digest="0" * 64)

    payload = dict(report.public_payload)
    payload["ready_ratio"] = "0.000000"
    with pytest.raises(ValueError, match="digest"):
        module.validate_research_acquisition_tool_readiness_report_public_payload(payload)

    unsafe = dict(report.public_payload)
    unsafe["source_url"] = "redacted"
    with pytest.raises(ValueError, match="public"):
        module.validate_research_acquisition_tool_readiness_report_public_payload(unsafe)


def test_module_is_readonly_report_only_and_has_no_runtime_surfaces() -> None:
    module = api()
    report = build_report()

    assert report.public_payload["paper_only"] is True
    assert report.public_payload["report_only"] is True
    assert report.public_payload["readonly"] is True

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }

