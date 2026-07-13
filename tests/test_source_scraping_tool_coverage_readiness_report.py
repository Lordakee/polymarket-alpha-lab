from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal, ROUND_DOWN, ROUND_UP, localcontext
import json
from pathlib import Path
from types import MappingProxyType

import pytest

import polymarket_alpha_lab.source_scraping_tool_coverage_readiness_report as module

from polymarket_alpha_lab.source_scraping_tool_coverage_readiness_report import (
    SourceScrapingToolCoverageReadinessInput,
    SourceScrapingToolCoverageReadinessReport,
    build_source_scraping_tool_coverage_readiness_report,
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _TupleSubclass(tuple):
    pass


class _ListSubclass(list):
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
    source_freshness_score: Decimal = d("1.000000"),
    source_family_diversity_score: Decimal = d("1.000000"),
    capture_completeness_score: Decimal = d("1.000000"),
) -> SourceScrapingToolCoverageReadinessInput:
    return SourceScrapingToolCoverageReadinessInput(
        agent_reach_available=agent_reach_available,
        scrapling_available=scrapling_available,
        official_api_available=official_api_available,
        browser_capture_available=browser_capture_available,
        source_snapshot_digest_present=source_snapshot_digest_present,
        fallback_path_count=fallback_path_count,
        source_freshness_score=source_freshness_score,
        source_family_diversity_score=source_family_diversity_score,
        capture_completeness_score=capture_completeness_score,
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
    assert readiness_report.source_freshness_score == d("1.000000")
    assert readiness_report.source_family_diversity_score == d("1.000000")
    assert readiness_report.capture_completeness_score == d("1.000000")
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
        "source_freshness_score": "1.000000",
        "source_family_diversity_score": "1.000000",
        "capture_completeness_score": "1.000000",
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


def test_public_payload_revalidates_the_stored_digest_on_every_access() -> None:
    pristine = report(tool_input())
    stale_digest = report(
        tool_input(source_freshness_score=d("0.900000")),
    ).payload_digest

    assert stale_digest != pristine.payload_digest

    constructor_sentinel = replace(pristine, payload_digest="")
    with pytest.raises(ValueError, match="payload_digest"):
        _ = constructor_sentinel.public_payload

    for forged_digest in ("", "0" * 64, stale_digest):
        digest_tampered = report(tool_input())
        object.__setattr__(digest_tampered, "payload_digest", forged_digest)
        with pytest.raises(ValueError, match="payload_digest"):
            _ = digest_tampered.public_payload

    content_tampered = report(tool_input())
    object.__setattr__(
        content_tampered,
        "source_freshness_score",
        d("0.900000"),
    )
    with pytest.raises(ValueError, match="payload_digest"):
        _ = content_tampered.public_payload


def test_ratio_rounding_status_and_digest_ignore_global_decimal_context() -> None:
    results: list[tuple[Decimal, str, tuple[str, ...], str]] = []

    for rounding in (ROUND_DOWN, ROUND_UP):
        with localcontext() as context:
            context.rounding = rounding
            readiness_report = report(
                tool_input(source_freshness_score=d("0.4999995")),
            )
        results.append(
            (
                readiness_report.source_freshness_score,
                readiness_report.coverage_status,
                readiness_report.reason_codes,
                readiness_report.payload_digest,
            ),
        )

    assert results[0] == results[1]
    assert results[0][:3] == (
        d("0.500000"),
        "watch",
        ("coverage_watch", "source_freshness_watch"),
    )


def test_whole_count_representation_is_canonical_for_payload_and_digest() -> None:
    integer_count = report(tool_input(fallback_path_count=d("2")))
    scaled_count = report(tool_input(fallback_path_count=d("2.000000")))

    assert integer_count.fallback_path_count.as_tuple().exponent == 0
    assert scaled_count.fallback_path_count.as_tuple().exponent == 0
    assert integer_count.public_payload == scaled_count.public_payload
    assert integer_count.payload_digest == scaled_count.payload_digest


def test_negative_zero_inputs_and_reports_share_one_positive_payload_and_digest() -> None:
    positive_input = tool_input(
        fallback_path_count=d("0"),
        source_freshness_score=d("0.000000"),
        source_family_diversity_score=d("0.000000"),
        capture_completeness_score=d("0.000000"),
    )
    negative_input = tool_input(
        fallback_path_count=d("-0"),
        source_freshness_score=d("-0.000000"),
        source_family_diversity_score=d("-0.000000"),
        capture_completeness_score=d("-0.000000"),
    )

    for value, quantum in (
        (negative_input.fallback_path_count, d("1")),
        (negative_input.source_freshness_score, d("0.000001")),
        (negative_input.source_family_diversity_score, d("0.000001")),
        (negative_input.capture_completeness_score, d("0.000001")),
    ):
        assert value.is_zero()
        assert not value.is_signed()
        assert value.same_quantum(quantum)

    positive_report = report(positive_input)
    negative_report = report(negative_input)
    for field_name in (
        "fallback_path_count",
        "source_freshness_score",
        "source_family_diversity_score",
        "capture_completeness_score",
        "tool_path_count",
    ):
        assert not getattr(negative_report, field_name).is_signed()
    assert negative_report.public_payload == positive_report.public_payload
    assert negative_report.payload_digest == positive_report.payload_digest


@pytest.mark.parametrize(
    ("field_name", "negative_zero"),
    (
        ("fallback_path_count", d("-0")),
        ("source_freshness_score", d("-0.000000")),
        ("source_family_diversity_score", d("-0.000000")),
        ("capture_completeness_score", d("-0.000000")),
        ("tool_path_count", d("-0")),
    ),
)
def test_public_payload_rejects_rehashed_negative_zero_stored_decimals(
    field_name: str,
    negative_zero: Decimal,
) -> None:
    forged = report(
        tool_input(
            agent_reach_available=False,
            scrapling_available=False,
            official_api_available=False,
            browser_capture_available=False,
            fallback_path_count=d("0"),
            source_freshness_score=d("0.000000"),
            source_family_diversity_score=d("0.000000"),
            capture_completeness_score=d("0.000000"),
        ),
    )
    object.__setattr__(forged, field_name, negative_zero)
    object.__setattr__(
        forged,
        "payload_digest",
        module._payload_digest(module._payload_without_digest(forged)),
    )

    with pytest.raises(ValueError, match=f"{field_name} must not be negative zero"):
        _ = forged.public_payload


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error", "single_tool"),
    (
        ("tool_path_count", True, "tool_path_count must be a Decimal", True),
        (
            "tool_path_count",
            _DecimalSubclass("4"),
            "tool_path_count must be a Decimal",
            False,
        ),
        ("coverage_status", _StringSubclass("ready"), "coverage_status", False),
        (
            "reason_codes",
            _TupleSubclass(("coverage_ready",)),
            "reason_codes",
            False,
        ),
        (
            "manual_next_step",
            _StringSubclass(
                "Continue paper-only source coverage review with the current tool map.",
            ),
            "manual_next_step",
            False,
        ),
    ),
)
def test_public_payload_rejects_non_exact_derived_field_types(
    field_name: str,
    forged_value: object,
    error: str,
    single_tool: bool,
) -> None:
    readiness_input = tool_input(
        scrapling_available=not single_tool,
        official_api_available=not single_tool,
        browser_capture_available=not single_tool,
        fallback_path_count=d("1") if single_tool else d("2"),
    )
    forged = report(readiness_input)
    object.__setattr__(forged, field_name, forged_value)
    object.__setattr__(
        forged,
        "payload_digest",
        module._payload_digest(module._payload_without_digest(forged)),
    )

    with pytest.raises(ValueError, match=error):
        _ = forged.public_payload


@pytest.mark.parametrize("field_name", ("paper_only", "report_only", "readonly"))
def test_public_payload_rejects_recomputed_false_report_flags(field_name: str) -> None:
    forged = report(tool_input())
    object.__setattr__(forged, field_name, False)
    object.__setattr__(
        forged,
        "payload_digest",
        module._payload_digest(module._payload_without_digest(forged)),
    )

    with pytest.raises(ValueError, match=field_name):
        _ = forged.public_payload


def test_payload_serializer_materializes_and_revalidates_public_mappings() -> None:
    payload = report(tool_input()).public_payload

    materialized = module.source_scraping_tool_coverage_readiness_report_payload(
        MappingProxyType(payload),
    )

    assert type(materialized) is dict
    assert materialized == payload
    assert materialized is not payload
    assert type(materialized["reason_codes"]) is list
    assert materialized["reason_codes"] is not payload["reason_codes"]


def test_payload_serializer_rejects_non_exact_mapping_keys() -> None:
    payload = report(tool_input()).public_payload
    agent_reach_available = payload.pop("agent_reach_available")
    payload[_StringSubclass("agent_reach_available")] = agent_reach_available
    with pytest.raises(ValueError, match="keys must be exact strings"):
        module.source_scraping_tool_coverage_readiness_report_payload(payload)


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error"),
    (
        ("paper_only", False, "paper_only"),
        ("tool_path_count", "True", "tool_path_count must be a Decimal string"),
        ("coverage_status", _StringSubclass("ready"), "coverage_status"),
        ("reason_codes", _ListSubclass(["coverage_ready"]), "reason_codes"),
        (
            "manual_next_step",
            _StringSubclass(
                "Continue paper-only source coverage review with the current tool map.",
            ),
            "manual_next_step",
        ),
    ),
)
def test_payload_serializer_rejects_non_exact_mapping_values(
    field_name: str,
    forged_value: object,
    error: str,
) -> None:
    forged = dict(report(tool_input()).public_payload)
    forged[field_name] = forged_value
    unsigned = dict(forged)
    del unsigned["payload_digest"]
    forged["payload_digest"] = module._payload_digest(unsigned)

    with pytest.raises(ValueError, match=error):
        module.source_scraping_tool_coverage_readiness_report_payload(forged)


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


def test_information_readiness_metrics_watch_and_block_before_strategy_use() -> None:
    watched = report(
        tool_input(
            source_freshness_score=d("0.700000"),
            source_family_diversity_score=d("0.650000"),
            capture_completeness_score=d("0.600000"),
        ),
    )
    blocked = report(
        tool_input(
            source_freshness_score=d("0.400000"),
            source_family_diversity_score=d("0.450000"),
            capture_completeness_score=d("0.250000"),
        ),
    )

    assert watched.coverage_status == "watch"
    assert watched.reason_codes == (
        "capture_completeness_watch",
        "coverage_watch",
        "source_family_diversity_watch",
        "source_freshness_watch",
    )
    assert (
        watched.manual_next_step
        == "Refresh sources, add independent families, or complete captures before strategy use."
    )
    assert watched.public_payload["source_freshness_score"] == "0.700000"
    assert watched.public_payload["source_family_diversity_score"] == "0.650000"
    assert watched.public_payload["capture_completeness_score"] == "0.600000"

    assert blocked.coverage_status == "blocked"
    assert blocked.reason_codes == (
        "capture_completeness_blocked",
        "coverage_blocked",
        "source_family_diversity_blocked",
        "source_freshness_blocked",
    )
    assert (
        blocked.manual_next_step
        == "Block strategy use until source freshness, family diversity, and capture completeness are repaired."
    )


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
    with pytest.raises(ValueError, match="source_freshness_score"):
        tool_input(source_freshness_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_family_diversity_score"):
        tool_input(source_family_diversity_score=d("1.000001"))
    with pytest.raises(ValueError, match="capture_completeness_score"):
        tool_input(capture_completeness_score=_DecimalSubclass("1.000000"))
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
