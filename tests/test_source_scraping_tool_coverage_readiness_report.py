from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.source_scraping_tool_coverage_readiness_report import (
    SourceScrapingToolCoverageReadinessInput,
    SourceScrapingToolCoverageReadinessReport,
    build_source_scraping_tool_coverage_readiness_report,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def tool_input(
    *,
    agent_reach_available: bool = True,
    scrapling_available: bool = True,
    official_api_available: bool = True,
    browser_capture_available: bool = True,
    source_snapshot_digest_present: bool = True,
    fallback_path_count: Decimal = d("2"),
) -> SourceScrapingToolCoverageReadinessInput:
    return SourceScrapingToolCoverageReadinessInput(
        agent_reach_available=agent_reach_available,
        scrapling_available=scrapling_available,
        official_api_available=official_api_available,
        browser_capture_available=browser_capture_available,
        source_snapshot_digest_present=source_snapshot_digest_present,
        fallback_path_count=fallback_path_count,
    )


def report(
    readiness_input: SourceScrapingToolCoverageReadinessInput,
) -> SourceScrapingToolCoverageReadinessReport:
    return build_source_scraping_tool_coverage_readiness_report(readiness_input)


def test_all_tool_surfaces_snapshot_and_fallbacks_are_ready_with_stable_digest() -> None:
    readiness_report = report(tool_input())
    payload = readiness_report.public_payload

    assert type(readiness_report) is SourceScrapingToolCoverageReadinessReport
    assert is_dataclass(readiness_report)
    assert readiness_report.agent_reach_available is True
    assert readiness_report.scrapling_available is True
    assert readiness_report.official_api_available is True
    assert readiness_report.browser_capture_available is True
    assert readiness_report.source_snapshot_digest_present is True
    assert readiness_report.fallback_path_count == d("2")
    assert readiness_report.tool_path_count == d("4")
    assert readiness_report.coverage_status == "ready"
    assert readiness_report.reason_codes == ("coverage_ready",)
    assert (
        readiness_report.manual_next_step
        == "Continue paper-only source coverage review with the current tool map."
    )
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True

    assert payload == {
        "agent_reach_available": True,
        "scrapling_available": True,
        "official_api_available": True,
        "browser_capture_available": True,
        "source_snapshot_digest_present": True,
        "fallback_path_count": "2",
        "tool_path_count": "4",
        "coverage_status": "ready",
        "reason_codes": ["coverage_ready"],
        "manual_next_step": "Continue paper-only source coverage review with the current tool map.",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": readiness_report.payload_digest,
    }
    assert readiness_report.payload_digest == report(tool_input()).payload_digest
    assert len(readiness_report.payload_digest) == 64
    assert all(character in "0123456789abcdef" for character in readiness_report.payload_digest)
    assert json.loads(json.dumps(payload)) == payload
    assert not any(type(value) is float for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))


def test_missing_secondary_tool_paths_are_watch_with_manual_next_step() -> None:
    readiness_report = report(
        tool_input(
            scrapling_available=False,
            official_api_available=False,
            browser_capture_available=False,
            fallback_path_count=d("1"),
        ),
    )

    assert readiness_report.tool_path_count == d("1")
    assert readiness_report.coverage_status == "watch"
    assert readiness_report.reason_codes == (
        "browser_capture_missing",
        "coverage_watch",
        "official_api_missing",
        "scrapling_missing",
        "single_collection_tool_path",
    )
    assert (
        readiness_report.manual_next_step
        == "Add missing readonly collection paths or record the manual review rationale."
    )
    assert readiness_report.public_payload["fallback_path_count"] == "1"
    assert readiness_report.public_payload["tool_path_count"] == "1"


def test_missing_required_snapshot_or_fallback_blocks_readiness() -> None:
    missing_snapshot = report(tool_input(source_snapshot_digest_present=False))
    missing_fallback = report(tool_input(fallback_path_count=d("0")))
    no_tools = report(
        tool_input(
            agent_reach_available=False,
            scrapling_available=False,
            official_api_available=False,
            browser_capture_available=False,
        ),
    )

    assert missing_snapshot.coverage_status == "blocked"
    assert "source_snapshot_digest_missing" in missing_snapshot.reason_codes
    assert (
        missing_snapshot.manual_next_step
        == "Add a public source snapshot digest before readiness review."
    )
    assert missing_fallback.coverage_status == "blocked"
    assert "fallback_path_missing" in missing_fallback.reason_codes
    assert (
        missing_fallback.manual_next_step
        == "Record at least one manual fallback path before relying on tool coverage."
    )
    assert no_tools.coverage_status == "blocked"
    assert "collection_tool_missing" in no_tools.reason_codes
    assert (
        no_tools.manual_next_step
        == "Add at least one readonly paper collection tool before source review."
    )


def test_rejects_non_decimal_counts_bad_flags_and_is_frozen() -> None:
    readiness_report = report(tool_input())

    with pytest.raises(FrozenInstanceError):
        readiness_report.coverage_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness_report.reason_codes = ("changed",)  # type: ignore[misc]
    with pytest.raises(ValueError, match="fallback_path_count"):
        tool_input(fallback_path_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fallback_path_count"):
        tool_input(fallback_path_count=d("1.5"))
    with pytest.raises(ValueError, match="fallback_path_count"):
        tool_input(fallback_path_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="agent_reach_available"):
        SourceScrapingToolCoverageReadinessInput(
            agent_reach_available=1,  # type: ignore[arg-type]
            scrapling_available=True,
            official_api_available=True,
            browser_capture_available=True,
            source_snapshot_digest_present=True,
            fallback_path_count=d("1"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(tool_input(), paper_only=False)


def test_owned_module_is_readonly_report_only_and_has_no_collection_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "source_scraping_tool_coverage_readiness_report.py"
    )
    source_code = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret_key",
        "签名",
        "执行路径",
    )

    assert all(term not in source_code for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for field_name, item in value.items():
            values.extend(_walk_payload_values(field_name))
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
