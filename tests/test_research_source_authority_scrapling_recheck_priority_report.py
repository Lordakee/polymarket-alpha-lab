from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_source_authority_scrapling_recheck_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "authority_watch_floor": d("0.750000"),
        "authority_block_floor": d("0.550000"),
        "scrapling_freshness_watch_age_seconds": d("1800.000000"),
        "scrapling_freshness_block_age_seconds": d("7200.000000"),
        "authority_revision_watch_age_seconds": d("86400.000000"),
        "authority_revision_block_age_seconds": d("172800.000000"),
        "extraction_confidence_watch_floor": d("0.800000"),
        "extraction_confidence_block_floor": d("0.600000"),
        "extractor_disagreement_watch_pressure": d("0.250000"),
        "extractor_disagreement_block_pressure": d("0.500000"),
        "primary_coverage_watch_floor": d("0.750000"),
        "primary_coverage_block_floor": d("0.500000"),
        "unresolved_claim_watch_count": d("1.000000"),
        "unresolved_claim_block_count": d("2.000000"),
        "failed_attempt_watch_count": d("1.000000"),
        "failed_attempt_block_count": d("3.000000"),
        "resolution_watch_seconds_remaining": d("7200.000000"),
        "resolution_block_seconds_remaining": d("1800.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityScraplingRecheckPriorityConfig(**values)


def recheck_item(
    recheck_bucket: str,
    *,
    source_authority_score: Decimal = d("1.000000"),
    scrapling_latest_success_age_seconds: Decimal = d("0.000000"),
    authority_revision_age_seconds: Decimal = d("0.000000"),
    scrapling_extraction_confidence_score: Decimal = d("1.000000"),
    cross_extractor_disagreement_score: Decimal = d("0.000000"),
    primary_evidence_coverage_ratio: Decimal = d("1.000000"),
    unresolved_claim_count: Decimal = d("0.000000"),
    failed_scrapling_attempt_count: Decimal = d("0.000000"),
    successful_scrapling_attempt_count: Decimal = d("4.000000"),
    resolution_seconds_remaining: Decimal = d("14400.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityScraplingRecheckPriorityInput(
        recheck_bucket=recheck_bucket,
        source_authority_score=source_authority_score,
        scrapling_latest_success_age_seconds=scrapling_latest_success_age_seconds,
        authority_revision_age_seconds=authority_revision_age_seconds,
        scrapling_extraction_confidence_score=scrapling_extraction_confidence_score,
        cross_extractor_disagreement_score=cross_extractor_disagreement_score,
        primary_evidence_coverage_ratio=primary_evidence_coverage_ratio,
        unresolved_claim_count=unresolved_claim_count,
        failed_scrapling_attempt_count=failed_scrapling_attempt_count,
        successful_scrapling_attempt_count=successful_scrapling_attempt_count,
        resolution_seconds_remaining=resolution_seconds_remaining,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_authority_scrapling_recheck_priority_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_report_is_pass_report_only_digest_validated_and_decimal_only() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceAuthorityScraplingRecheckPriorityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.recheck_item_count == d("0.000000")
    assert report.pass_recheck_item_count == d("0.000000")
    assert report.watch_recheck_item_count == d("0.000000")
    assert report.block_recheck_item_count == d("0.000000")
    assert report.low_authority_count == d("0.000000")
    assert report.stale_scrapling_count == d("0.000000")
    assert report.stale_authority_revision_count == d("0.000000")
    assert report.low_extraction_confidence_count == d("0.000000")
    assert report.extractor_disagreement_count == d("0.000000")
    assert report.thin_primary_coverage_count == d("0.000000")
    assert report.unresolved_claim_count == d("0.000000")
    assert report.failed_attempt_pressure_count == d("0.000000")
    assert report.resolution_proximity_count == d("0.000000")
    assert report.highest_recheck_priority_score == d("0.000000")
    assert report.oldest_scrapling_latest_success_age_seconds == d("0.000000")
    assert report.oldest_authority_revision_age_seconds == d("0.000000")
    assert report.lowest_source_authority_score == d("0.000000")
    assert report.lowest_scrapling_extraction_confidence_score == d("0.000000")
    assert report.highest_cross_extractor_disagreement_score == d("0.000000")
    assert report.lowest_primary_evidence_coverage_ratio == d("0.000000")
    assert report.nearest_resolution_seconds_remaining == d("0.000000")
    assert report.reason_codes == (
        "research_source_authority_scrapling_recheck_priority_empty",
    )
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_source_authority_scrapling_recheck_priority_report_digest(report)
    )
    module.validate_research_source_authority_scrapling_recheck_priority_report_digest(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_recheck_priority_scores_authority_scrapling_and_resolution_pressure() -> None:
    report = build_report(
        recheck_item("official_primary"),
        recheck_item(
            "wire_followup",
            source_authority_score=d("0.700000"),
            scrapling_latest_success_age_seconds=d("3600.000000"),
            authority_revision_age_seconds=d("100000.000000"),
            scrapling_extraction_confidence_score=d("0.750000"),
            cross_extractor_disagreement_score=d("0.300000"),
            primary_evidence_coverage_ratio=d("0.700000"),
            unresolved_claim_count=d("1.000000"),
            failed_scrapling_attempt_count=d("1.000000"),
            successful_scrapling_attempt_count=d("3.000000"),
            resolution_seconds_remaining=d("3600.000000"),
        ),
        recheck_item(
            "official_recheck",
            source_authority_score=d("0.400000"),
            scrapling_latest_success_age_seconds=d("8000.000000"),
            authority_revision_age_seconds=d("200000.000000"),
            scrapling_extraction_confidence_score=d("0.500000"),
            cross_extractor_disagreement_score=d("0.700000"),
            primary_evidence_coverage_ratio=d("0.400000"),
            unresolved_claim_count=d("2.000000"),
            failed_scrapling_attempt_count=d("3.000000"),
            successful_scrapling_attempt_count=d("1.000000"),
            resolution_seconds_remaining=d("1200.000000"),
        ),
    )

    assert report.status == "block"
    assert report.recheck_item_count == d("3.000000")
    assert report.pass_recheck_item_count == d("1.000000")
    assert report.watch_recheck_item_count == d("1.000000")
    assert report.block_recheck_item_count == d("1.000000")
    assert report.low_authority_count == d("2.000000")
    assert report.stale_scrapling_count == d("2.000000")
    assert report.stale_authority_revision_count == d("2.000000")
    assert report.low_extraction_confidence_count == d("2.000000")
    assert report.extractor_disagreement_count == d("2.000000")
    assert report.thin_primary_coverage_count == d("2.000000")
    assert report.unresolved_claim_count == d("2.000000")
    assert report.failed_attempt_pressure_count == d("2.000000")
    assert report.resolution_proximity_count == d("2.000000")
    assert report.highest_recheck_priority_score == d("0.756667")
    assert report.oldest_scrapling_latest_success_age_seconds == d("8000.000000")
    assert report.oldest_authority_revision_age_seconds == d("200000.000000")
    assert report.lowest_source_authority_score == d("0.400000")
    assert report.lowest_scrapling_extraction_confidence_score == d("0.500000")
    assert report.highest_cross_extractor_disagreement_score == d("0.700000")
    assert report.lowest_primary_evidence_coverage_ratio == d("0.400000")
    assert report.nearest_resolution_seconds_remaining == d("1200.000000")
    assert tuple(row.recheck_bucket for row in report.rows) == (
        "official_recheck",
        "wire_followup",
        "official_primary",
    )
    assert report.reason_codes == (
        "research_source_authority_scrapling_recheck_priority_low_authority_block",
        "research_source_authority_scrapling_recheck_priority_stale_scrapling_block",
        "research_source_authority_scrapling_recheck_priority_stale_authority_revision_block",
        "research_source_authority_scrapling_recheck_priority_low_extraction_confidence_block",
        "research_source_authority_scrapling_recheck_priority_extractor_disagreement_block",
        "research_source_authority_scrapling_recheck_priority_thin_primary_coverage_block",
        "research_source_authority_scrapling_recheck_priority_unresolved_claim_block",
        "research_source_authority_scrapling_recheck_priority_failed_attempt_block",
        "research_source_authority_scrapling_recheck_priority_resolution_proximity_block",
        "research_source_authority_scrapling_recheck_priority_low_authority_watch",
        "research_source_authority_scrapling_recheck_priority_stale_scrapling_watch",
        "research_source_authority_scrapling_recheck_priority_stale_authority_revision_watch",
        "research_source_authority_scrapling_recheck_priority_low_extraction_confidence_watch",
        "research_source_authority_scrapling_recheck_priority_extractor_disagreement_watch",
        "research_source_authority_scrapling_recheck_priority_thin_primary_coverage_watch",
        "research_source_authority_scrapling_recheck_priority_unresolved_claim_watch",
        "research_source_authority_scrapling_recheck_priority_failed_attempt_watch",
        "research_source_authority_scrapling_recheck_priority_resolution_proximity_watch",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.authority_band == "low"
    assert blocked.scrapling_freshness_band == "stale"
    assert blocked.authority_revision_band == "stale"
    assert blocked.failed_attempt_pressure_score == d("0.750000")
    assert blocked.resolution_pressure_score == d("0.833333")
    assert blocked.recheck_priority_score == d("0.756667")

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.authority_band == "medium"
    assert watched.scrapling_freshness_band == "aging"
    assert watched.authority_revision_band == "aging"
    assert watched.failed_attempt_pressure_score == d("0.250000")
    assert watched.resolution_pressure_score == d("0.500000")
    assert watched.recheck_priority_score == d("0.379838")

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.authority_band == "high"
    assert passed.scrapling_freshness_band == "fresh"
    assert passed.authority_revision_band == "current"
    assert passed.recheck_priority_score == d("0.000000")
    assert passed.reason_codes == (
        "research_source_authority_scrapling_recheck_priority_clear",
    )


def test_status_vocabulary_is_only_pass_watch_block() -> None:
    module = api()
    pass_report = build_report(recheck_item("official_primary"))
    watch_report = build_report(
        recheck_item("wire_followup", source_authority_score=d("0.700000")),
    )
    block_report = build_report(
        recheck_item(
            "official_recheck",
            cross_extractor_disagreement_score=d("0.700000"),
        ),
    )

    assert module.RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert pass_report.status == "pass"
    assert pass_report.rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"


def test_payload_and_digest_are_deterministic_json_ready_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        recheck_item("official_primary"),
        recheck_item(
            "official_recheck",
            source_authority_score=d("0.400000"),
            scrapling_latest_success_age_seconds=d("8000.000000"),
            authority_revision_age_seconds=d("200000.000000"),
            scrapling_extraction_confidence_score=d("0.500000"),
            cross_extractor_disagreement_score=d("0.700000"),
            primary_evidence_coverage_ratio=d("0.400000"),
            unresolved_claim_count=d("2.000000"),
            failed_scrapling_attempt_count=d("3.000000"),
            successful_scrapling_attempt_count=d("1.000000"),
            resolution_seconds_remaining=d("1200.000000"),
        ),
    )
    report_b = build_report(
        recheck_item(
            "official_recheck",
            source_authority_score=d("0.400000"),
            scrapling_latest_success_age_seconds=d("8000.000000"),
            authority_revision_age_seconds=d("200000.000000"),
            scrapling_extraction_confidence_score=d("0.500000"),
            cross_extractor_disagreement_score=d("0.700000"),
            primary_evidence_coverage_ratio=d("0.400000"),
            unresolved_claim_count=d("2.000000"),
            failed_scrapling_attempt_count=d("3.000000"),
            successful_scrapling_attempt_count=d("1.000000"),
            resolution_seconds_remaining=d("1200.000000"),
        ),
        recheck_item("official_primary"),
    )

    payload_a = module.research_source_authority_scrapling_recheck_priority_report_payload(
        report_a,
    )
    payload_b = module.research_source_authority_scrapling_recheck_priority_report_payload(
        report_b,
    )
    digest_a = module.research_source_authority_scrapling_recheck_priority_report_digest(
        report_a,
    )
    digest_b = module.research_source_authority_scrapling_recheck_priority_report_digest(
        report_b,
    )

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_a["recheck_item_count"] == "2.000000"
    assert (
        payload_a["rows"][0]["recheck_priority_score"]
        >= payload_a["rows"][1]["recheck_priority_score"]
    )
    json.dumps(payload_a, sort_keys=True)
    assert_no_public_numeric_values(payload_a)
    assert tuple(payload_a) == tuple(field.name for field in fields(type(report_a)))
    assert tuple(payload_a["rows"][0]) == tuple(
        field.name for field in fields(type(report_a.rows[0]))
    )

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
        "recommended_size",
        "recommendation",
    }
    keys = {
        field.name
        for cls in (type(report_a), type(report_a.rows[0]))
        for field in fields(cls)
    }
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_rejects_non_decimal_inputs_unsafe_labels_flags_and_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="authority_watch_floor must be a Decimal"):
        config(authority_watch_floor=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        recheck_item("official_primary", source_authority_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unresolved_claim_count must be a Decimal"):
        recheck_item("official_primary", unresolved_claim_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unresolved_claim_count must be a whole Decimal"):
        recheck_item("official_primary", unresolved_claim_count=d("1.500000"))
    with pytest.raises(ValueError, match="authority_revision_age_seconds must be nonnegative"):
        recheck_item("official_primary", authority_revision_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="recheck_bucket contains unsafe text"):
        recheck_item("candidate-123")
    with pytest.raises(ValueError, match="recheck_bucket contains unsafe text"):
        recheck_item("market_slug")
    with pytest.raises(ValueError, match="recheck_bucket contains unsafe text"):
        recheck_item("https://example.invalid/path")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_authority_scrapling_recheck_priority_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        recheck_item("official_primary", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        recheck_item("official_primary", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        recheck_item("official_primary", readonly=False)

    report = build_report(recheck_item("official_primary"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="clear")


def test_signed_zero_is_rejected_and_decimal_arithmetic_uses_fixed_context() -> None:
    with pytest.raises(ValueError, match="source_authority_score must not use signed zero"):
        recheck_item("signed-zero", source_authority_score=d("-0"))
    with pytest.raises(ValueError, match="resolution_seconds_remaining must not use signed zero"):
        recheck_item("signed-zero-time", resolution_seconds_remaining=d("-0"))

    with localcontext(Context(prec=1)):
        report = build_report(recheck_item("low-context"))

    assert report.recheck_item_count == d("1.000000")
    assert report.rows[0].recheck_priority_score == d("0.000000")
    assert not report.recheck_item_count.is_signed()
    assert not report.rows[0].recheck_priority_score.is_signed()


def test_public_dataclasses_are_final_frozen_and_have_exact_field_schemas() -> None:
    module = api()
    expected_fields = {
        module.ResearchSourceAuthorityScraplingRecheckPriorityConfig: (
            "config_version",
            "authority_watch_floor",
            "authority_block_floor",
            "scrapling_freshness_watch_age_seconds",
            "scrapling_freshness_block_age_seconds",
            "authority_revision_watch_age_seconds",
            "authority_revision_block_age_seconds",
            "extraction_confidence_watch_floor",
            "extraction_confidence_block_floor",
            "extractor_disagreement_watch_pressure",
            "extractor_disagreement_block_pressure",
            "primary_coverage_watch_floor",
            "primary_coverage_block_floor",
            "unresolved_claim_watch_count",
            "unresolved_claim_block_count",
            "failed_attempt_watch_count",
            "failed_attempt_block_count",
            "resolution_watch_seconds_remaining",
            "resolution_block_seconds_remaining",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceAuthorityScraplingRecheckPriorityInput: (
            "recheck_bucket",
            "source_authority_score",
            "scrapling_latest_success_age_seconds",
            "authority_revision_age_seconds",
            "scrapling_extraction_confidence_score",
            "cross_extractor_disagreement_score",
            "primary_evidence_coverage_ratio",
            "unresolved_claim_count",
            "failed_scrapling_attempt_count",
            "successful_scrapling_attempt_count",
            "resolution_seconds_remaining",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceAuthorityScraplingRecheckPriorityRow: (
            "recheck_bucket",
            "source_authority_score",
            "authority_band",
            "scrapling_latest_success_age_seconds",
            "scrapling_freshness_band",
            "authority_revision_age_seconds",
            "authority_revision_band",
            "scrapling_extraction_confidence_score",
            "cross_extractor_disagreement_score",
            "primary_evidence_coverage_ratio",
            "unresolved_claim_count",
            "failed_scrapling_attempt_count",
            "successful_scrapling_attempt_count",
            "failed_attempt_pressure_score",
            "resolution_seconds_remaining",
            "resolution_pressure_score",
            "recheck_priority_score",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceAuthorityScraplingRecheckPriorityReport: (
            "generated_at",
            "config_version",
            "recheck_item_count",
            "pass_recheck_item_count",
            "watch_recheck_item_count",
            "block_recheck_item_count",
            "low_authority_count",
            "stale_scrapling_count",
            "stale_authority_revision_count",
            "low_extraction_confidence_count",
            "extractor_disagreement_count",
            "thin_primary_coverage_count",
            "unresolved_claim_count",
            "failed_attempt_pressure_count",
            "resolution_proximity_count",
            "highest_recheck_priority_score",
            "oldest_scrapling_latest_success_age_seconds",
            "oldest_authority_revision_age_seconds",
            "lowest_source_authority_score",
            "lowest_scrapling_extraction_confidence_score",
            "highest_cross_extractor_disagreement_score",
            "lowest_primary_evidence_coverage_ratio",
            "nearest_resolution_seconds_remaining",
            "status",
            "reason_codes",
            "rows",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }

    for cls, field_names in expected_fields.items():
        assert getattr(cls, "__final__", False) is True
        assert tuple(field.name for field in fields(cls)) == field_names
        assert cls.__dataclass_params__.frozen is True


def test_public_validation_rejects_resigned_derived_row_forgery() -> None:
    module = api()
    report = build_report(
        recheck_item(
            "tampered-derived-row",
            source_authority_score=d("0.700000"),
            resolution_seconds_remaining=d("3600.000000"),
        ),
    )
    row = report.rows[0]
    object.__setattr__(row, "resolution_pressure_score", d("0.000000"))
    forged_payload = module._json_ready(report)
    forged_payload.pop("derived_validation_digest")
    object.__setattr__(
        report,
        "derived_validation_digest",
        module._canonical_digest(forged_payload),
    )

    with pytest.raises(ValueError, match="resolution_pressure_score"):
        module.validate_research_source_authority_scrapling_recheck_priority_report_digest(
            report,
        )


def test_public_validation_rederives_reason_codes_and_rejects_bypassed_config() -> None:
    module = api()
    report = build_report(
        recheck_item(
            "tampered-reasons",
            source_authority_score=d("0.700000"),
        ),
    )
    row = report.rows[0]
    object.__setattr__(row, "status", "pass")
    object.__setattr__(row, "reason_codes", (module.CLEAR_REASON,))
    forged_payload = module._json_ready(report)
    forged_payload.pop("derived_validation_digest")
    object.__setattr__(
        report,
        "derived_validation_digest",
        module._canonical_digest(forged_payload),
    )

    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        module.validate_research_source_authority_scrapling_recheck_priority_report_digest(
            report,
        )

    bypassed_config = config()
    object.__setattr__(
        bypassed_config,
        "resolution_block_seconds_remaining",
        d("9000.000000"),
    )
    with pytest.raises(ValueError, match="resolution_block_seconds_remaining"):
        build_report(recheck_item("bypassed-config"), cfg=bypassed_config)


def test_exports_frozen_dataclasses_and_public_api() -> None:
    module = api()
    report = build_report(recheck_item("official_primary"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_STATUSES",
        "ResearchSourceAuthorityScraplingRecheckPriorityConfig",
        "ResearchSourceAuthorityScraplingRecheckPriorityInput",
        "ResearchSourceAuthorityScraplingRecheckPriorityReport",
        "ResearchSourceAuthorityScraplingRecheckPriorityRow",
        "build_research_source_authority_scrapling_recheck_priority_report",
        "research_source_authority_scrapling_recheck_priority_report_digest",
        "research_source_authority_scrapling_recheck_priority_report_payload",
        "validate_research_source_authority_scrapling_recheck_priority_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(recheck_item("official_primary"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().authority_watch_floor = d("0.800000")


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
        "auth",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "wallet",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)
    else:
        assert type(value) is not float
        assert type(value) is not int


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "candidate_id",
        "raw_candidate",
        "market-",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "source_url",
        "source_text",
        " table",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
        "sizing",
        "recommendation",
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
