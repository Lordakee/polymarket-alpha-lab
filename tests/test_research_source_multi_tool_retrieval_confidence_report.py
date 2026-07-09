from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_multi_tool_retrieval_confidence_report as api
from polymarket_alpha_lab.research_source_multi_tool_retrieval_confidence_report import (
    ResearchSourceMultiToolRetrievalConfidenceConfig,
    ResearchSourceMultiToolRetrievalConfidenceObservation,
    ResearchSourceMultiToolRetrievalConfidenceReport,
    build_research_source_multi_tool_retrieval_confidence_report,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _observation(
    retrieval_scope: str = "macro-calendar",
    tool_name: str = "scrapling",
    *,
    observed_at: datetime | None = None,
    coverage_ratio: Decimal = d("1.000000"),
    extraction_confidence: Decimal = d("1.000000"),
    contradiction_pressure: Decimal = d("0.000000"),
    authority_score: Decimal = d("1.000000"),
) -> ResearchSourceMultiToolRetrievalConfidenceObservation:
    return ResearchSourceMultiToolRetrievalConfidenceObservation(
        retrieval_scope=retrieval_scope,
        tool_name=tool_name,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        coverage_ratio=coverage_ratio,
        extraction_confidence=extraction_confidence,
        contradiction_pressure=contradiction_pressure,
        authority_score=authority_score,
    )


def _report(
    observations: tuple[ResearchSourceMultiToolRetrievalConfidenceObservation, ...],
    *,
    config: ResearchSourceMultiToolRetrievalConfidenceConfig | None = None,
) -> ResearchSourceMultiToolRetrievalConfidenceReport:
    return build_research_source_multi_tool_retrieval_confidence_report(
        observations,
        config=config or ResearchSourceMultiToolRetrievalConfidenceConfig(),
        generated_at=GENERATED_AT,
    )


def _rows_by_scope(
    report: ResearchSourceMultiToolRetrievalConfidenceReport,
) -> dict[str, api.ResearchSourceMultiToolRetrievalConfidenceRow]:
    return {row.retrieval_scope: row for row in report.rows}


def test_retrieval_confidence_scoring_builds_pass_watch_and_block_rows() -> None:
    report = _report(
        (
            _observation(
                "macro-calendar-pass",
                "scrapling",
                extraction_confidence=d("0.950000"),
                contradiction_pressure=d("0.050000"),
            ),
            _observation(
                "macro-calendar-pass",
                "agent_reach",
                extraction_confidence=d("0.950000"),
                contradiction_pressure=d("0.050000"),
            ),
            _observation(
                "macro-calendar-pass",
                "browser_capture",
                extraction_confidence=d("0.950000"),
                contradiction_pressure=d("0.050000"),
            ),
            _observation(
                "macro-calendar-pass",
                "fallback",
                extraction_confidence=d("0.950000"),
                contradiction_pressure=d("0.050000"),
            ),
            _observation(
                "macro-calendar-watch",
                "scrapling",
                coverage_ratio=d("0.750000"),
                extraction_confidence=d("0.700000"),
                contradiction_pressure=d("0.300000"),
                authority_score=d("0.850000"),
            ),
            _observation(
                "macro-calendar-watch",
                "agent_reach",
                coverage_ratio=d("0.750000"),
                extraction_confidence=d("0.700000"),
                contradiction_pressure=d("0.300000"),
                authority_score=d("0.850000"),
            ),
            _observation(
                "macro-calendar-block",
                "fallback",
                observed_at=GENERATED_AT - timedelta(days=2),
                coverage_ratio=d("0.400000"),
                extraction_confidence=d("0.450000"),
                contradiction_pressure=d("0.750000"),
                authority_score=d("0.350000"),
            ),
        ),
    )

    assert report.status == "block"
    assert report.retrieval_scope_count == d("3.000000")
    assert report.observation_count == d("7.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_retrieval_confidence_score == d("0.659167")
    assert report.lowest_retrieval_confidence_score == d("0.202500")
    assert report.max_contradiction_pressure == d("0.750000")
    assert report.max_retrieval_age_seconds == d("172800.000000")

    rows = _rows_by_scope(report)
    pass_row = rows["macro-calendar-pass"]
    assert pass_row.status == "pass"
    assert pass_row.tool_count == d("4.000000")
    assert pass_row.core_tool_count == d("3.000000")
    assert pass_row.fallback_tool_count == d("1.000000")
    assert pass_row.coverage_score == d("1.000000")
    assert pass_row.freshness_score == d("1.000000")
    assert pass_row.extraction_confidence == d("0.950000")
    assert pass_row.contradiction_pressure == d("0.050000")
    assert pass_row.authority_mix_score == d("1.000000")
    assert pass_row.fallback_penalty == d("0.000000")
    assert pass_row.retrieval_confidence_score == d("0.980000")
    assert pass_row.reason_codes == ("multi_tool_retrieval_confidence_pass",)

    watch_row = rows["macro-calendar-watch"]
    assert watch_row.status == "watch"
    assert watch_row.coverage_score == d("0.750000")
    assert watch_row.extraction_confidence == d("0.700000")
    assert watch_row.contradiction_pressure == d("0.300000")
    assert watch_row.authority_mix_score == d("0.850000")
    assert watch_row.retrieval_confidence_score == d("0.795000")
    assert watch_row.reason_codes == (
        "multi_tool_retrieval_confidence_watch",
        "coverage_below_pass_threshold",
        "extraction_confidence_below_pass_threshold",
        "contradiction_pressure_above_pass_threshold",
    )

    block_row = rows["macro-calendar-block"]
    assert block_row.status == "block"
    assert block_row.coverage_score == d("0.400000")
    assert block_row.freshness_score == d("0.000000")
    assert block_row.extraction_confidence == d("0.450000")
    assert block_row.contradiction_pressure == d("0.750000")
    assert block_row.authority_mix_score == d("0.350000")
    assert block_row.fallback_penalty == d("0.100000")
    assert block_row.retrieval_confidence_score == d("0.202500")
    assert block_row.reason_codes == (
        "multi_tool_retrieval_confidence_block",
        "coverage_below_block_threshold",
        "freshness_below_block_threshold",
        "extraction_confidence_below_block_threshold",
        "contradiction_pressure_above_block_threshold",
        "authority_mix_below_block_threshold",
        "core_tool_mix_below_block_threshold",
        "fallback_penalty_applied",
    )


def test_fallback_penalty_can_move_otherwise_strong_retrieval_to_watch() -> None:
    config = ResearchSourceMultiToolRetrievalConfidenceConfig(
        fallback_tool_penalty=d("0.200000"),
        minimum_core_tool_pass_count=d("0.000000"),
        minimum_core_tool_block_count=d("0.000000"),
    )
    report = _report(
        (
            _observation("core-only", "browser_capture"),
            _observation("fallback-only", "fallback"),
        ),
        config=config,
    )
    rows = _rows_by_scope(report)

    assert rows["core-only"].fallback_penalty == d("0.000000")
    assert rows["core-only"].retrieval_confidence_score == d("1.000000")
    assert rows["core-only"].status == "pass"
    assert rows["fallback-only"].fallback_penalty == d("0.200000")
    assert rows["fallback-only"].retrieval_confidence_score == d("0.800000")
    assert rows["fallback-only"].status == "watch"
    assert rows["fallback-only"].reason_codes == (
        "multi_tool_retrieval_confidence_watch",
        "retrieval_confidence_score_below_pass_threshold",
        "fallback_penalty_applied",
    )


def test_public_payload_digest_is_deterministic_and_validates_tampering() -> None:
    observations = (
        _observation("macro-calendar-pass", "scrapling"),
        _observation("macro-calendar-pass", "agent_reach"),
        _observation("macro-calendar-watch", "browser_capture", coverage_ratio=d("0.750000")),
    )
    report = _report(observations)
    same_report = _report(tuple(reversed(observations)))
    changed_report = _report(
        (
            _observation("macro-calendar-pass", "scrapling"),
            _observation("macro-calendar-pass", "agent_reach"),
            _observation(
                "macro-calendar-watch",
                "browser_capture",
                coverage_ratio=d("0.740000"),
            ),
        ),
    )

    assert report.public_digest == same_report.public_digest
    assert report.public_digest != changed_report.public_digest

    payload = api.research_source_multi_tool_retrieval_confidence_report_public_payload(
        report,
    )
    assert payload == report.public_payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["retrieval_scope_count"] == "2.000000"
    assert payload["rows"][0]["retrieval_confidence_score"] == "1.000000"
    assert payload["public_digest"] == report.public_digest
    assert len(payload["public_digest"]) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)
    api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
        payload,
    )

    tampered_payload = dict(payload)
    tampered_payload["pass_count"] = "99.000000"
    with pytest.raises(ValueError, match="public_digest"):
        api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
            tampered_payload,
        )
    with pytest.raises(ValueError, match="public_digest"):
        api.research_source_multi_tool_retrieval_confidence_report_public_payload(
            tampered_payload,
        )


def test_public_payload_prevents_sensitive_surface_leaks_and_dataclasses_are_frozen() -> None:
    report = _report((_observation(),))
    payload = report.public_payload
    forbidden_fragments = (
        "candidate_id",
        "candidate-id",
        "market_id",
        "market-id",
        "market_slug",
        "market-slug",
        "slug",
        "question",
        "source_url",
        "source-url",
        "source_text",
        "source-text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
        "http://",
        "https://",
        "www.",
    )

    for public_name in (*api.__all__, *_walk_strings(payload)):
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ResearchSourceMultiToolRetrievalConfidenceConfig,
        ResearchSourceMultiToolRetrievalConfidenceObservation,
        api.ResearchSourceMultiToolRetrievalConfidenceRow,
        ResearchSourceMultiToolRetrievalConfidenceReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="unsafe public"):
        _observation(retrieval_scope="market_slug_123")
    with pytest.raises(ValueError, match="unsafe public"):
        _observation(retrieval_scope="https://example.test/research")

    unsafe_payload = dict(payload)
    unsafe_payload["source_url"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
            unsafe_payload,
        )


def test_public_payload_validation_rejects_status_values_outside_report_set() -> None:
    report = _report((_observation(),))
    payload = report.public_payload

    invalid_report_status_payload = _with_recomputed_digest(
        payload,
        status="ok",
    )
    with pytest.raises(ValueError, match="status"):
        api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
            invalid_report_status_payload,
        )

    invalid_row_status_payload = dict(payload)
    invalid_row_status_payload["rows"] = [
        dict(row, status="ok") for row in payload["rows"]
    ]
    invalid_row_status_payload = _with_recomputed_digest(invalid_row_status_payload)
    with pytest.raises(ValueError, match="status"):
        api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
            invalid_row_status_payload,
        )


def test_public_payload_validation_rejects_unrecognized_fields() -> None:
    report = _report((_observation(),))
    payload = report.public_payload

    extra_top_level_payload = _with_recomputed_digest(
        payload,
        topic="fed-rate-cut-july-2026",
    )
    with pytest.raises(ValueError, match="unexpected public payload field"):
        api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
            extra_top_level_payload,
        )

    extra_row_payload = dict(payload)
    extra_row_payload["rows"] = [
        dict(row, topic="fed-rate-cut-july-2026") for row in payload["rows"]
    ]
    extra_row_payload = _with_recomputed_digest(extra_row_payload)
    with pytest.raises(ValueError, match="unexpected row payload field"):
        api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
            extra_row_payload,
        )


def test_public_payload_validation_rejects_generic_auth_and_db_surfaces() -> None:
    report = _report((_observation(),))
    payload = report.public_payload

    for unsafe_key in (
        "auth",
        "db",
        "password",
        "file_path",
        "postgres",
        "endpoint",
    ):
        unsafe_payload = _with_recomputed_digest(
            payload,
            **{unsafe_key: "enabled"},
        )
        with pytest.raises(ValueError, match="unsafe public"):
            api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
                unsafe_payload,
            )


def test_public_payload_validation_rejects_noncanonical_and_inconsistent_values() -> None:
    report = _report((_observation(),))
    payload = report.public_payload

    invalid_top_level_values = (
        ({"retrieval_scope_count": "1"}, "retrieval_scope_count"),
        ({"observation_count": "2.000000"}, "observation_count"),
        (
            {"average_retrieval_confidence_score": "0.500000"},
            "average_retrieval_confidence_score",
        ),
        ({"generated_at": "2026-07-08T12:00:00"}, "generated_at"),
        ({"config_version": "unsupported"}, "config_version"),
        ({"status": "watch"}, "status"),
    )
    for overrides, error_match in invalid_top_level_values:
        invalid_payload = _with_recomputed_digest(payload, **overrides)
        with pytest.raises(ValueError, match=error_match):
            api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
                invalid_payload,
            )

    invalid_row_values = (
        ({"retrieval_scope": "macro calendar"}, "retrieval_scope"),
        ({"tool_count": "1.500000", "core_tool_count": "1.500000"}, "tool_count"),
        ({"latest_observed_at": "2026-07-08T11:30:00"}, "latest_observed_at"),
        ({"coverage_score": "1.100000"}, "coverage_score"),
        (
            {
                "status": "watch",
                "reason_codes": ["multi_tool_retrieval_confidence_watch"],
            },
            "reason_codes",
        ),
    )
    for row_overrides, error_match in invalid_row_values:
        invalid_payload = dict(payload)
        invalid_payload["rows"] = [dict(payload["rows"][0], **row_overrides)]
        invalid_payload = _with_recomputed_digest(invalid_payload)
        with pytest.raises(ValueError, match=error_match):
            api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
                invalid_payload,
            )

    tuple_reason_codes_payload = dict(payload)
    tuple_reason_codes_payload["rows"] = [
        dict(
            payload["rows"][0],
            reason_codes=tuple(payload["rows"][0]["reason_codes"]),
        ),
    ]
    with pytest.raises(ValueError, match="lists"):
        api.validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
            tuple_reason_codes_payload,
        )


def test_manual_rows_and_reports_reject_inconsistent_derived_values() -> None:
    report = _report((_observation(),))
    row = report.rows[0]

    with pytest.raises(ValueError, match="tool_count"):
        replace(
            row,
            tool_count=d("0.000000"),
            core_tool_count=d("0.000000"),
        )
    with pytest.raises(ValueError, match="tool_count"):
        replace(
            row,
            tool_count=d("1.500000"),
            core_tool_count=d("1.500000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row,
            status="watch",
            reason_codes=("multi_tool_retrieval_confidence_watch",),
        )
    with pytest.raises(ValueError, match="observation_count"):
        replace(
            report,
            observation_count=d("2.000000"),
            public_digest="",
        )
    with pytest.raises(ValueError, match="pass_count"):
        replace(
            report,
            pass_count=d("0.000000"),
            block_count=d("1.000000"),
            public_digest="",
        )
    with pytest.raises(ValueError, match="average_retrieval_confidence_score"):
        replace(
            report,
            average_retrieval_confidence_score=d("0.500000"),
            public_digest="",
        )
    with pytest.raises(ValueError, match="max_retrieval_age_seconds"):
        replace(
            report,
            max_retrieval_age_seconds=d("1.000000"),
            public_digest="",
        )


def test_phase1_datetime_boundaries_require_timezone_awareness() -> None:
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _observation(observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_source_multi_tool_retrieval_confidence_report(
            (_observation(),),
            config=ResearchSourceMultiToolRetrievalConfidenceConfig(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )


def test_custom_config_validation_rejects_non_decimal_and_bad_thresholds() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceMultiToolRetrievalConfidenceConfig(
            coverage_weight=0.25,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="sum to 1"):
        ResearchSourceMultiToolRetrievalConfidenceConfig(
            coverage_weight=d("0.300000"),
        )
    with pytest.raises(ValueError, match="pass_retrieval_confidence_score"):
        ResearchSourceMultiToolRetrievalConfidenceConfig(
            pass_retrieval_confidence_score=d("0.400000"),
            watch_retrieval_confidence_score=d("0.400000"),
        )
    with pytest.raises(ValueError, match="minimum_core_tool_block_count"):
        ResearchSourceMultiToolRetrievalConfidenceConfig(
            minimum_core_tool_pass_count=d("1.000000"),
            minimum_core_tool_block_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceMultiToolRetrievalConfidenceConfig(paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        _observation(coverage_ratio=0.5)  # type: ignore[arg-type]

    strict_config = ResearchSourceMultiToolRetrievalConfidenceConfig(
        pass_retrieval_confidence_score=d("0.990000"),
    )
    strict_report = _report(
        (_observation(extraction_confidence=d("0.950000")),),
        config=strict_config,
    )
    assert strict_report.rows[0].status == "watch"
    assert strict_report.rows[0].reason_codes == (
        "multi_tool_retrieval_confidence_watch",
        "retrieval_confidence_score_below_pass_threshold",
    )


def _with_recomputed_digest(
    payload: dict[str, object],
    **overrides: object,
) -> dict[str, object]:
    copied = json.loads(json.dumps(payload, sort_keys=True))
    copied.update(overrides)
    copied["public_digest"] = (
        api.research_source_multi_tool_retrieval_confidence_report_public_digest(copied)
    )
    return copied


def _walk_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            strings.extend(_walk_strings(key))
            strings.extend(_walk_strings(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            strings.extend(_walk_strings(item))
    return tuple(strings)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        pytest.fail("public payload must serialize Decimal values as strings")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, Decimal):
        return
    if isinstance(value, (int, float)):
        pytest.fail(f"public report numeric must be Decimal-only: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_non_decimal_public_numbers(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
    elif hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
