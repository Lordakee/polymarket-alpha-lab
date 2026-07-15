from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, getcontext
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_fallback_coverage_gap_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_fallback_coverage_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "max_fallback_age_seconds": d("3600.000000"),
        "block_fallback_age_seconds": d("10800.000000"),
        "fallback_authority_watch_threshold": d("0.700000"),
        "fallback_authority_block_threshold": d("0.400000"),
        "minimum_corroboration_depth": d("2.000000"),
        "contradiction_watch_threshold": d("0.350000"),
        "contradiction_block_threshold": d("0.700000"),
        "extraction_confidence_watch_threshold": d("0.800000"),
        "extraction_confidence_block_threshold": d("0.500000"),
        "deadline_watch_seconds": d("7200.000000"),
        "deadline_block_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceFallbackCoverageGapConfig(**values)


def signal(
    review_scope: str,
    *,
    primary_source_available: bool = False,
    fallback_available: bool = True,
    observed_seconds_ago: int | None = 900,
    fallback_authority_score: Decimal = d("0.950000"),
    corroboration_depth: Decimal = d("3.000000"),
    contradiction_pressure: Decimal = d("0.100000"),
    extraction_confidence: Decimal = d("0.900000"),
    deadline_seconds_from_now: int | None = 20000,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceFallbackCoverageSignal(
        review_scope=review_scope,
        primary_source_available=primary_source_available,
        fallback_available=fallback_available,
        fallback_observed_at=(
            None
            if observed_seconds_ago is None
            else GENERATED_AT - timedelta(seconds=observed_seconds_ago)
        ),
        fallback_authority_score=fallback_authority_score,
        corroboration_depth=corroboration_depth,
        contradiction_pressure=contradiction_pressure,
        extraction_confidence=extraction_confidence,
        decision_deadline_at=(
            None
            if deadline_seconds_from_now is None
            else GENERATED_AT + timedelta(seconds=deadline_seconds_from_now)
        ),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_fallback_coverage_gap_report(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_blocks_without_exposing_sensitive_public_surfaces() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceFallbackCoverageGapReport
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.review_scope_count == d("0.000000")
    assert report.primary_source_gap_count == d("0.000000")
    assert report.fallback_available_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.max_coverage_gap_score == d("0.000000")
    assert report.lowest_fallback_readiness_score == d("0.000000")
    assert report.highest_fallback_age_seconds == d("0.000000")
    assert report.reason_codes == ("no_fallback_coverage_scopes",)
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert report.derived_validation_digest == (
        module.research_source_fallback_coverage_gap_report_digest(report)
    )
    assert module.validate_research_source_fallback_coverage_gap_report_digest(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.research_source_fallback_coverage_gap_report_payload(report)
    assert_no_unsafe_public_payload(payload)
    assert_no_float_or_int_values(payload)


def test_fallback_coverage_scores_pass_watch_and_block_dimensions() -> None:
    report = build_report(
        signal("covered-primary-gap"),
        signal(
            "thin-fallback-gap",
            observed_seconds_ago=5400,
            fallback_authority_score=d("0.650000"),
            corroboration_depth=d("1.000000"),
            contradiction_pressure=d("0.400000"),
            extraction_confidence=d("0.750000"),
            deadline_seconds_from_now=3600,
        ),
        signal(
            "blocked-fallback-gap",
            fallback_available=False,
            observed_seconds_ago=None,
            fallback_authority_score=d("0.300000"),
            corroboration_depth=d("0.000000"),
            contradiction_pressure=d("0.800000"),
            extraction_confidence=d("0.400000"),
            deadline_seconds_from_now=900,
        ),
        signal(
            "primary-intact",
            primary_source_available=True,
            fallback_available=False,
            observed_seconds_ago=None,
            fallback_authority_score=d("0.000000"),
            corroboration_depth=d("0.000000"),
            contradiction_pressure=d("1.000000"),
            extraction_confidence=d("0.000000"),
            deadline_seconds_from_now=900,
        ),
    )

    assert report.status == "block"
    assert report.review_scope_count == d("4.000000")
    assert report.primary_source_gap_count == d("3.000000")
    assert report.fallback_available_count == d("2.000000")
    assert report.fresh_fallback_count == d("1.000000")
    assert report.authoritative_fallback_count == d("1.000000")
    assert report.corroborated_fallback_count == d("1.000000")
    assert report.confident_extraction_count == d("1.000000")
    assert report.deadline_pressure_count == d("2.000000")
    assert report.pass_count == d("2.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.max_coverage_gap_score == d("1.000000")
    assert report.lowest_fallback_readiness_score == d("0.150000")
    assert report.highest_fallback_age_seconds == d("5400.000000")
    assert report.reason_codes == (
        "contradiction_pressure_block",
        "contradiction_pressure_watch",
        "corroboration_depth_block",
        "corroboration_depth_watch",
        "deadline_proximity_block",
        "deadline_proximity_watch",
        "extraction_confidence_block",
        "extraction_confidence_watch",
        "fallback_authority_block",
        "fallback_authority_watch",
        "missing_fallback_source",
        "stale_fallback_watch",
    )

    blocked, watched, covered, primary = report.rows
    assert (blocked.review_scope, blocked.status) == ("blocked-fallback-gap", "block")
    assert blocked.fallback_age_seconds is None
    assert blocked.deadline_seconds_remaining == d("900.000000")
    assert blocked.deadline_proximity_score == d("1.000000")
    assert blocked.fallback_readiness_score == d("0.150000")
    assert blocked.coverage_gap_score == d("1.000000")
    assert blocked.reason_codes == (
        "fallback_coverage_gap_block",
        "contradiction_pressure_block",
        "corroboration_depth_block",
        "deadline_proximity_block",
        "extraction_confidence_block",
        "fallback_authority_block",
        "missing_fallback_source",
    )

    assert (watched.review_scope, watched.status) == ("thin-fallback-gap", "watch")
    assert watched.fallback_age_seconds == d("5400.000000")
    assert watched.fallback_freshness_score == d("0.500000")
    assert watched.corroboration_score == d("0.500000")
    assert watched.deadline_proximity_score == d("0.666667")
    assert watched.fallback_readiness_score == d("0.666667")
    assert watched.coverage_gap_score == d("0.666667")
    assert watched.reason_codes == (
        "fallback_coverage_gap_watch",
        "contradiction_pressure_watch",
        "corroboration_depth_watch",
        "deadline_proximity_watch",
        "extraction_confidence_watch",
        "fallback_authority_watch",
        "stale_fallback_watch",
    )

    assert (covered.review_scope, covered.status) == ("covered-primary-gap", "pass")
    assert covered.fallback_age_seconds == d("900.000000")
    assert covered.fallback_freshness_score == d("1.000000")
    assert covered.corroboration_score == d("1.000000")
    assert covered.fallback_readiness_score == d("0.958333")
    assert covered.coverage_gap_score == d("0.041667")
    assert covered.reason_codes == ("fallback_coverage_gap_pass",)

    assert (primary.review_scope, primary.status) == ("primary-intact", "pass")
    assert primary.fallback_readiness_score == d("1.000000")
    assert primary.coverage_gap_score == d("0.000000")
    assert primary.reason_codes == ("fallback_coverage_gap_pass",)


def test_payload_is_deterministic_immutable_json_ready_and_digest_validated() -> None:
    module = api()
    report_a = build_report(
        signal("covered-primary-gap"),
        signal(
            "thin-fallback-gap",
            observed_seconds_ago=5400,
            fallback_authority_score=d("0.650000"),
            corroboration_depth=d("1.000000"),
            contradiction_pressure=d("0.400000"),
            extraction_confidence=d("0.750000"),
            deadline_seconds_from_now=3600,
        ),
    )
    report_b = build_report(
        signal(
            "thin-fallback-gap",
            observed_seconds_ago=5400,
            fallback_authority_score=d("0.650000"),
            corroboration_depth=d("1.000000"),
            contradiction_pressure=d("0.400000"),
            extraction_confidence=d("0.750000"),
            deadline_seconds_from_now=3600,
        ),
        signal("covered-primary-gap"),
    )

    payload_a = module.research_source_fallback_coverage_gap_report_payload(report_a)
    payload_b = module.research_source_fallback_coverage_gap_report_payload(report_b)
    digest_a = module.research_source_fallback_coverage_gap_report_digest(report_a)

    assert payload_a == payload_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["review_scope_count"] == "2.000000"
    assert payload_a["rows"][0]["review_scope"] == "thin-fallback-gap"
    assert payload_a["rows"][0]["coverage_gap_score"] == "0.666667"
    json.dumps(payload_a, sort_keys=True)
    assert_no_unsafe_public_payload(payload_a)
    assert_no_float_or_int_values(payload_a)

    with pytest.raises(TypeError, match="immutable"):
        payload_a["status"] = "pass"
    with pytest.raises(TypeError, match="immutable"):
        payload_a["rows"].append({})
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_rejects_bad_numeric_types_flags_timestamps_and_public_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="max_fallback_age_seconds"):
        config(max_fallback_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fallback_authority_watch_threshold"):
        config(fallback_authority_watch_threshold=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="block_fallback_age_seconds"):
        config(block_fallback_age_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="deadline_watch_seconds"):
        config(deadline_watch_seconds=d("1800.000000"))
    with pytest.raises(ValueError, match="review_scope"):
        signal("market_slug_yes_2026")
    with pytest.raises(ValueError, match="review_scope"):
        signal("https://example.test/source")
    with pytest.raises(ValueError, match="review_scope"):
        signal("candidate_id_123")
    with pytest.raises(ValueError, match="fallback_authority_score"):
        signal("covered-gap", fallback_authority_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="corroboration_depth"):
        signal("covered-gap", corroboration_depth=d("1.500000"))
    with pytest.raises(ValueError, match="contradiction_pressure"):
        signal("covered-gap", contradiction_pressure=d("1.500000"))
    with pytest.raises(ValueError, match="extraction_confidence"):
        signal("covered-gap", extraction_confidence=d("-0.100000"))
    with pytest.raises(ValueError, match="fallback_observed_at"):
        build_report(signal("future-fallback", observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="paper_only"):
        signal("covered-gap", paper_only=False)

    report = build_report(signal("covered-gap"))
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):
        class _BadRow(module.ResearchSourceFallbackCoverageGapRow):  # type: ignore[misc, valid-type]
            pass


def test_decimal_contract_rejects_signed_zero_and_excess_precision_and_is_context_fixed() -> None:
    module = api()

    with pytest.raises(ValueError, match="fallback_authority_watch_threshold"):
        config(fallback_authority_watch_threshold=d("0.7000001"))
    with pytest.raises(ValueError, match="fallback_authority_score"):
        signal("signed-zero", fallback_authority_score=d("-0.000000"))

    original_precision = getcontext().prec
    try:
        getcontext().prec = 4
        report = build_report(
            signal(
                "precision-fixed",
                fallback_authority_score=d("0.650000"),
                corroboration_depth=d("1.000000"),
                contradiction_pressure=d("0.400000"),
                extraction_confidence=d("0.750000"),
                observed_seconds_ago=5400,
                deadline_seconds_from_now=3600,
            ),
        )
    finally:
        getcontext().prec = original_precision

    assert report.rows[0].fallback_freshness_score == d("0.500000")
    assert report.rows[0].deadline_proximity_score == d("0.666667")
    assert report.rows[0].fallback_readiness_score == d("0.666667")


def test_object_setattr_tampering_is_rejected_at_all_public_boundaries() -> None:
    module = api()
    cfg = config()
    input_signal = signal("mutation-input")
    report = build_report(input_signal, cfg=cfg)

    object.__setattr__(cfg, "max_fallback_age_seconds", d("1800.000000"))
    with pytest.raises(ValueError, match="modified after initialization"):
        build_report(signal("mutation-config"), cfg=cfg)

    snapshot_cfg = config()
    object.__setattr__(snapshot_cfg, "max_fallback_age_seconds", d("1800.000000"))
    object.__setattr__(
        snapshot_cfg,
        "_canonical_public_snapshot",
        module._public_snapshot(snapshot_cfg),
    )
    with pytest.raises(ValueError, match="modified after initialization"):
        build_report(signal("mutation-snapshot"), cfg=snapshot_cfg)

    object.__setattr__(input_signal, "fallback_authority_score", d("0.900000"))
    with pytest.raises(ValueError, match="modified after initialization"):
        build_report(input_signal)

    row = report.rows[0]
    object.__setattr__(row, "coverage_gap_score", d("0.000000"))
    with pytest.raises(ValueError, match="modified after initialization"):
        replace(report, rows=(row,))

    reason_count = report.reason_code_counts[0]
    object.__setattr__(reason_count, "count", d("99.000000"))
    with pytest.raises(ValueError, match="modified after initialization"):
        replace(report, reason_code_counts=(reason_count,))


def test_public_dataclasses_are_frozen_exact_final_types() -> None:
    module = api()
    public_types = (
        module.ResearchSourceFallbackCoverageGapConfig,
        module.ResearchSourceFallbackCoverageGapInput,
        module.ResearchSourceFallbackCoverageSignal,
        module.ResearchSourceFallbackCoverageGapRow,
        module.ResearchSourceFallbackCoverageGapReasonCodeCount,
        module.ResearchSourceFallbackCoverageGapReport,
    )
    for public_type in public_types:
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Derived{public_type.__name__}", (public_type,), {})


def test_public_mapping_is_schema_ordered_and_rederives_every_observational_field() -> None:
    module = api()
    report = build_report(signal("mapping-observation"))
    payload = json.loads(
        json.dumps(module.research_source_fallback_coverage_gap_report_payload(report)),
    )

    rebuilt = module.research_source_fallback_coverage_gap_report_payload(payload)
    assert dict(rebuilt) == payload

    with pytest.raises(ValueError, match="canonical key order"):
        module.research_source_fallback_coverage_gap_report_payload(
            dict(reversed(tuple(payload.items()))),
        )

    tampered = json.loads(json.dumps(payload))
    tampered["rows"][0]["coverage_gap_score"] = "0.000000"
    _resign_payload(tampered)
    with pytest.raises(ValueError, match="coverage_gap_score"):
        module.research_source_fallback_coverage_gap_report_payload(tampered)


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    (
        ("fallback_authority_score", "0.900000"),
        ("fallback_age_seconds", "0.000000"),
        ("fallback_freshness_score", "0.000000"),
        ("corroboration_score", "0.000000"),
        ("deadline_seconds_remaining", "0.000000"),
        ("deadline_proximity_score", "1.000000"),
        ("fallback_readiness_score", "0.000000"),
        ("status", "watch"),
        (
            "reason_codes",
            ["fallback_coverage_gap_watch", "fallback_authority_watch"],
        ),
    ),
)
def test_resigned_public_mapping_rejects_each_row_observational_derivation(
    field_name: str,
    replacement: object,
) -> None:
    module = api()
    payload = json.loads(
        json.dumps(
            module.research_source_fallback_coverage_gap_report_payload(
                build_report(signal("resigned-observation")),
            ),
        ),
    )
    payload["rows"][0][field_name] = replacement
    _resign_payload(payload)

    with pytest.raises(ValueError):
        module.research_source_fallback_coverage_gap_report_payload(payload)


def test_resigned_public_mapping_rejects_aggregate_counts_reason_counts_and_order() -> None:
    module = api()
    payload = json.loads(
        json.dumps(
            module.research_source_fallback_coverage_gap_report_payload(
                build_report(signal("sort-a"), signal("sort-b")),
            ),
        ),
    )

    aggregate_tamper = json.loads(json.dumps(payload))
    aggregate_tamper["review_scope_count"] = "0.000000"
    _resign_payload(aggregate_tamper)
    with pytest.raises(ValueError, match="review_scope_count"):
        module.research_source_fallback_coverage_gap_report_payload(aggregate_tamper)

    count_tamper = json.loads(json.dumps(payload))
    count_tamper["reason_code_counts"][0]["count"] = "99.000000"
    _resign_payload(count_tamper)
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_source_fallback_coverage_gap_report_payload(count_tamper)

    ordering_tamper = json.loads(json.dumps(payload))
    ordering_tamper["rows"].reverse()
    _resign_payload(ordering_tamper)
    with pytest.raises(ValueError, match="deterministic sorting"):
        module.research_source_fallback_coverage_gap_report_payload(ordering_tamper)


def test_module_imports_no_network_database_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_roots = {
        "asyncpg",
        "boto3",
        "httpx",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlalchemy",
        "subprocess",
        "urllib",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(forbidden_roots)


def assert_no_float_or_int_values(payload: object) -> None:
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))


def assert_no_unsafe_public_payload(payload: object) -> None:
    unsafe_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "raw_url",
        "url",
        "source_text",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "http://",
        "https://",
        "www.",
    )
    for key, value in _walk_payload_items(payload):
        lowered_key = key.lower()
        assert not any(fragment in lowered_key for fragment in unsafe_fragments)
        if type(value) is str:
            lowered_value = value.lower()
            assert not any(fragment in lowered_value for fragment in unsafe_fragments)


def _walk_payload_items(value: object) -> tuple[tuple[str, object], ...]:
    items: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            items.append((key, item))
            items.extend(_walk_payload_items(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            items.extend(_walk_payload_items(item))
    return tuple(items)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(_walk_payload_values(item))
    return tuple(values)


def _resign_payload(payload: dict[str, object]) -> None:
    rows = payload["rows"]
    assert type(rows) is list
    for row in rows:
        assert type(row) is dict
        row_payload = {
            key: value
            for key, value in row.items()
            if key != "derived_validation_digest"
        }
        row["derived_validation_digest"] = _sha256_payload(row_payload)
    report_payload = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    payload["derived_validation_digest"] = _sha256_payload(report_payload)


def _sha256_payload(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
