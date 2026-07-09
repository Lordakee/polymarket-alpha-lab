from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_primary_resolution_signal_completeness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "authority_coverage_watch_threshold": d("0.750000"),
        "authority_coverage_block_threshold": d("0.500000"),
        "freshness_watch_age_seconds": d("1800.000000"),
        "freshness_block_age_seconds": d("7200.000000"),
        "corroboration_watch_threshold": d("0.650000"),
        "corroboration_block_threshold": d("0.400000"),
        "contradiction_watch_threshold": d("0.300000"),
        "contradiction_block_threshold": d("0.600000"),
        "extraction_confidence_watch_threshold": d("0.750000"),
        "extraction_confidence_block_threshold": d("0.550000"),
        "deadline_watch_seconds_remaining": d("3600.000000"),
        "deadline_block_seconds_remaining": d("900.000000"),
    }
    values.update(overrides)
    return module.ResearchSourcePrimaryResolutionSignalCompletenessConfig(**values)


def signal(
    signal_family: str,
    *,
    authority_coverage_score: Decimal = d("0.900000"),
    signal_freshness_seconds: Decimal = d("600.000000"),
    corroboration_score: Decimal = d("0.850000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    extraction_confidence_score: Decimal = d("0.900000"),
    deadline_seconds_remaining: Decimal = d("7200.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourcePrimaryResolutionSignalCompletenessInput(
        signal_family=signal_family,
        authority_coverage_score=authority_coverage_score,
        signal_freshness_seconds=signal_freshness_seconds,
        corroboration_score=corroboration_score,
        contradiction_pressure_score=contradiction_pressure_score,
        extraction_confidence_score=extraction_confidence_score,
        deadline_seconds_remaining=deadline_seconds_remaining,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_primary_resolution_signal_completeness_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourcePrimaryResolutionSignalCompletenessReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.signal_family_count == d("0.000000")
    assert report.pass_signal_family_count == d("0.000000")
    assert report.watch_signal_family_count == d("0.000000")
    assert report.block_signal_family_count == d("0.000000")
    assert report.low_authority_coverage_count == d("0.000000")
    assert report.stale_signal_count == d("0.000000")
    assert report.thin_corroboration_count == d("0.000000")
    assert report.contradiction_pressure_count == d("0.000000")
    assert report.low_extraction_confidence_count == d("0.000000")
    assert report.deadline_proximity_count == d("0.000000")
    assert report.highest_resolution_signal_gap_score == d("0.000000")
    assert report.lowest_authority_coverage_score == d("0.000000")
    assert report.oldest_signal_freshness_seconds == d("0.000000")
    assert report.lowest_corroboration_score == d("0.000000")
    assert report.highest_contradiction_pressure_score == d("0.000000")
    assert report.lowest_extraction_confidence_score == d("0.000000")
    assert report.nearest_deadline_seconds_remaining == d("0.000000")
    assert report.reason_codes == (
        "research_source_primary_resolution_signal_completeness_empty",
    )
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_source_primary_resolution_signal_completeness_report_digest(
            report,
        )
    )
    module.validate_research_source_primary_resolution_signal_completeness_report_digest(
        report,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_signal_completeness_scores_all_review_readiness_pressures() -> None:
    report = build_report(
        signal(
            "official.final",
            authority_coverage_score=d("0.900000"),
            signal_freshness_seconds=d("600.000000"),
            corroboration_score=d("0.850000"),
            contradiction_pressure_score=d("0.050000"),
            extraction_confidence_score=d("0.900000"),
            deadline_seconds_remaining=d("7200.000000"),
        ),
        signal(
            "analyst.secondary",
            authority_coverage_score=d("0.700000"),
            signal_freshness_seconds=d("2400.000000"),
            corroboration_score=d("0.600000"),
            contradiction_pressure_score=d("0.350000"),
            extraction_confidence_score=d("0.700000"),
            deadline_seconds_remaining=d("1800.000000"),
        ),
        signal(
            "registry.audit",
            authority_coverage_score=d("0.450000"),
            signal_freshness_seconds=d("8000.000000"),
            corroboration_score=d("0.300000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_confidence_score=d("0.500000"),
            deadline_seconds_remaining=d("600.000000"),
        ),
    )

    assert report.status == "block"
    assert report.signal_family_count == d("3.000000")
    assert report.pass_signal_family_count == d("1.000000")
    assert report.watch_signal_family_count == d("1.000000")
    assert report.block_signal_family_count == d("1.000000")
    assert report.low_authority_coverage_count == d("2.000000")
    assert report.stale_signal_count == d("2.000000")
    assert report.thin_corroboration_count == d("2.000000")
    assert report.contradiction_pressure_count == d("2.000000")
    assert report.low_extraction_confidence_count == d("2.000000")
    assert report.deadline_proximity_count == d("2.000000")
    assert report.highest_resolution_signal_gap_score == d("0.688333")
    assert report.lowest_authority_coverage_score == d("0.450000")
    assert report.oldest_signal_freshness_seconds == d("8000.000000")
    assert report.lowest_corroboration_score == d("0.300000")
    assert report.highest_contradiction_pressure_score == d("0.700000")
    assert report.lowest_extraction_confidence_score == d("0.500000")
    assert report.nearest_deadline_seconds_remaining == d("600.000000")
    assert report.reason_codes == (
        "low_authority_coverage_block",
        "stale_primary_resolution_signal_block",
        "thin_corroboration_block",
        "contradiction_pressure_block",
        "low_extraction_confidence_block",
        "deadline_proximity_block",
        "low_authority_coverage_watch",
        "stale_primary_resolution_signal_watch",
        "thin_corroboration_watch",
        "contradiction_pressure_watch",
        "low_extraction_confidence_watch",
        "deadline_proximity_watch",
    )

    assert tuple(row.signal_family for row in report.rows) == (
        "registry.audit",
        "analyst.secondary",
        "official.final",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.authority_coverage_band == "gap"
    assert blocked.freshness_band == "stale"
    assert blocked.corroboration_band == "missing"
    assert blocked.contradiction_pressure_band == "high"
    assert blocked.extraction_confidence_band == "low"
    assert blocked.deadline_proximity_band == "immediate"
    assert blocked.deadline_pressure_score == d("0.833333")
    assert blocked.resolution_signal_gap_score == d("0.688333")
    assert blocked.reason_codes == (
        "low_authority_coverage_block",
        "stale_primary_resolution_signal_block",
        "thin_corroboration_block",
        "contradiction_pressure_block",
        "low_extraction_confidence_block",
        "deadline_proximity_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.authority_coverage_band == "partial"
    assert watched.freshness_band == "aging"
    assert watched.corroboration_band == "thin"
    assert watched.contradiction_pressure_band == "elevated"
    assert watched.extraction_confidence_band == "medium"
    assert watched.deadline_proximity_band == "near"
    assert watched.deadline_pressure_score == d("0.500000")
    assert watched.resolution_signal_gap_score == d("0.350000")
    assert watched.reason_codes == (
        "low_authority_coverage_watch",
        "stale_primary_resolution_signal_watch",
        "thin_corroboration_watch",
        "contradiction_pressure_watch",
        "low_extraction_confidence_watch",
        "deadline_proximity_watch",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.authority_coverage_band == "covered"
    assert passed.freshness_band == "fresh"
    assert passed.corroboration_band == "strong"
    assert passed.contradiction_pressure_band == "low"
    assert passed.extraction_confidence_band == "high"
    assert passed.deadline_proximity_band == "open"
    assert passed.resolution_signal_gap_score == d("0.085000")
    assert passed.reason_codes == ("primary_resolution_signal_complete",)


def test_watch_thresholds_are_statused_without_blocking() -> None:
    report = build_report(
        signal(
            "review.secondary",
            authority_coverage_score=d("0.700000"),
            signal_freshness_seconds=d("2400.000000"),
            corroboration_score=d("0.600000"),
            contradiction_pressure_score=d("0.350000"),
            extraction_confidence_score=d("0.700000"),
            deadline_seconds_remaining=d("1800.000000"),
        ),
    )

    assert report.status == "watch"
    assert report.watch_signal_family_count == d("1.000000")
    assert report.block_signal_family_count == d("0.000000")
    assert report.reason_codes == (
        "low_authority_coverage_watch",
        "stale_primary_resolution_signal_watch",
        "thin_corroboration_watch",
        "contradiction_pressure_watch",
        "low_extraction_confidence_watch",
        "deadline_proximity_watch",
    )
    assert report.rows[0].reason_codes == report.reason_codes


def test_payload_and_digest_are_deterministic_json_ready_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        signal("official.final"),
        signal(
            "registry.audit",
            authority_coverage_score=d("0.450000"),
            signal_freshness_seconds=d("8000.000000"),
            corroboration_score=d("0.300000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_confidence_score=d("0.500000"),
            deadline_seconds_remaining=d("600.000000"),
        ),
    )
    report_b = build_report(
        signal(
            "registry.audit",
            authority_coverage_score=d("0.450000"),
            signal_freshness_seconds=d("8000.000000"),
            corroboration_score=d("0.300000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_confidence_score=d("0.500000"),
            deadline_seconds_remaining=d("600.000000"),
        ),
        signal("official.final"),
    )

    payload_a = module.research_source_primary_resolution_signal_completeness_report_payload(
        report_a,
    )
    payload_b = module.research_source_primary_resolution_signal_completeness_report_payload(
        report_b,
    )
    digest_a = module.research_source_primary_resolution_signal_completeness_report_digest(
        report_a,
    )
    digest_b = module.research_source_primary_resolution_signal_completeness_report_digest(
        report_b,
    )

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["signal_family_count"] == "2.000000"
    assert payload_a["rows"][0]["resolution_signal_gap_score"] >= payload_a["rows"][1][
        "resolution_signal_gap_score"
    ]
    json.dumps(payload_a, sort_keys=True)
    assert_no_float_values(payload_a)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
    }
    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_public_payload_validator_enforces_exact_nested_schema_and_digest() -> None:
    module = api()
    report = build_report(signal("official.final"))
    payload = module.research_source_primary_resolution_signal_completeness_report_payload(
        report,
    )

    assert (
        module.validate_research_source_primary_resolution_signal_completeness_report_public_payload(
            payload,
        )
        is True
    )
    assert payload["derived_validation_digest"] == canonical_digest(payload)

    extra_top_level = dict(payload)
    extra_top_level["safe_extra"] = "redacted"
    extra_top_level["derived_validation_digest"] = canonical_digest(extra_top_level)

    missing_rows = dict(payload)
    missing_rows.pop("rows")
    missing_rows["derived_validation_digest"] = canonical_digest(missing_rows)

    wrong_rows_type = dict(payload)
    wrong_rows_type["rows"] = "redacted"
    wrong_rows_type["derived_validation_digest"] = canonical_digest(wrong_rows_type)

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["safe_extra"] = "redacted"
    extra_row_field["derived_validation_digest"] = canonical_digest(extra_row_field)

    raw_numeric = json.loads(json.dumps(payload))
    raw_numeric["rows"][0]["authority_coverage_score"] = 1
    raw_numeric["derived_validation_digest"] = canonical_digest(raw_numeric)

    inconsistent_band = json.loads(json.dumps(payload))
    inconsistent_band["rows"][0]["authority_coverage_band"] = "partial"
    inconsistent_band["derived_validation_digest"] = canonical_digest(inconsistent_band)

    inconsistent_gap_score = json.loads(json.dumps(payload))
    inconsistent_gap_score["rows"][0]["resolution_signal_gap_score"] = "0.100000"
    inconsistent_gap_score["highest_resolution_signal_gap_score"] = "0.100000"
    inconsistent_gap_score["derived_validation_digest"] = canonical_digest(
        inconsistent_gap_score,
    )

    for tampered_payload in (
        extra_top_level,
        missing_rows,
        wrong_rows_type,
        extra_row_field,
        raw_numeric,
        inconsistent_band,
        inconsistent_gap_score,
    ):
        assert (
            module.validate_research_source_primary_resolution_signal_completeness_report_public_payload(
                tampered_payload,
            )
            is False
        )

    object.__setattr__(report, "status", "watch")
    with pytest.raises(ValueError, match="status|derived_validation_digest"):
        module.research_source_primary_resolution_signal_completeness_report_digest(
            report,
        )


def test_negative_zero_decimal_inputs_are_canonicalized() -> None:
    module = api()
    report = build_report(
        signal(
            "official.final",
            authority_coverage_score=d("-0.000000"),
            signal_freshness_seconds=d("-0.000000"),
            corroboration_score=d("-0.000000"),
            contradiction_pressure_score=d("-0.000000"),
            extraction_confidence_score=d("-0.000000"),
            deadline_seconds_remaining=d("-0.000000"),
        ),
    )
    payload = module.research_source_primary_resolution_signal_completeness_report_payload(
        report,
    )

    assert "-0.000000" not in json.dumps(payload, sort_keys=True)
    assert (
        module.validate_research_source_primary_resolution_signal_completeness_report_public_payload(
            payload,
        )
        is True
    )


def test_validation_rejects_public_numeric_non_decimals_flags_and_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="freshness_block_age_seconds must be a Decimal"):
        config(freshness_block_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="authority_coverage_score must use six decimal places"):
        signal("official.final", authority_coverage_score=d("0.9"))
    with pytest.raises(ValueError, match="authority_coverage_score must be a Decimal"):
        signal("official.final", authority_coverage_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="signal_freshness_seconds must be a Decimal"):
        signal("official.final", signal_freshness_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="deadline_seconds_remaining must be nonnegative"):
        signal("official.final", deadline_seconds_remaining=d("-1.000000"))
    with pytest.raises(ValueError, match="freshness_watch_age_seconds must be positive"):
        config(freshness_watch_age_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="signal_family contains unsafe text"):
        signal("https://source.example/path")
    with pytest.raises(ValueError, match="signal_family contains unsafe text"):
        signal("market.slug")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_primary_resolution_signal_completeness_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        signal("official.final", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal("official.final", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        signal("official.final", readonly=False)

    report = build_report(signal("official.final"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="clear")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")


def test_builder_revalidates_mutated_config_and_input_instances() -> None:
    module = api()
    cfg = config()
    input_row = signal("official.final")

    object.__setattr__(cfg, "authority_coverage_watch_threshold", d("0.9"))
    with pytest.raises(
        ValueError,
        match="authority_coverage_watch_threshold must use six decimal places",
    ):
        module.build_research_source_primary_resolution_signal_completeness_report(
            (input_row,),
            config=cfg,
            generated_at=GENERATED_AT,
        )

    cfg = config()
    object.__setattr__(input_row, "authority_coverage_score", 0.9)
    with pytest.raises(ValueError, match="authority_coverage_score must be a Decimal"):
        module.build_research_source_primary_resolution_signal_completeness_report(
            (input_row,),
            config=cfg,
            generated_at=GENERATED_AT,
        )


def test_exports_frozen_dataclasses_and_status_vocabulary() -> None:
    module = api()
    report = build_report(signal("official.final"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_PRIMARY_RESOLUTION_SIGNAL_COMPLETENESS_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_PRIMARY_RESOLUTION_SIGNAL_COMPLETENESS_STATUSES",
        "ResearchSourcePrimaryResolutionSignalCompletenessConfig",
        "ResearchSourcePrimaryResolutionSignalCompletenessInput",
        "ResearchSourcePrimaryResolutionSignalCompletenessReport",
        "ResearchSourcePrimaryResolutionSignalCompletenessRow",
        "build_research_source_primary_resolution_signal_completeness_report",
        "research_source_primary_resolution_signal_completeness_report_digest",
        "research_source_primary_resolution_signal_completeness_report_payload",
        "validate_research_source_primary_resolution_signal_completeness_report_digest",
        "validate_research_source_primary_resolution_signal_completeness_report_public_payload",
    )
    assert module.RESEARCH_SOURCE_PRIMARY_RESOLUTION_SIGNAL_COMPLETENESS_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(signal("official.final"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().freshness_block_age_seconds = d("1.000000")


def test_module_scope_is_pure_public_safe_report_only() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
    else:
        assert type(value) is not float


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "market-",
        "token",
        "wallet",
        "order",
        "trade",
        "question",
        "table",
        "dsn",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()
