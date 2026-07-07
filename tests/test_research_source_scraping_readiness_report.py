from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_scraping_readiness_report import (
    ResearchSourceScrapingReadinessConfig,
    ResearchSourceScrapingReadinessReasonCodeCount,
    ResearchSourceScrapingReadinessReport,
    ResearchSourceScrapingReadinessRow,
    ResearchSourceScrapingReadinessSource,
    build_research_source_scraping_readiness_report,
    research_source_scraping_readiness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceScrapingReadinessConfig:
    values = {
        "config_version": "research-source-scraping-readiness-report-v0",
        "pass_readiness_score": d("0.800000"),
        "watch_readiness_score": d("0.500000"),
        "allowability_weight": d("0.250000"),
        "structure_weight": d("0.250000"),
        "cadence_weight": d("0.200000"),
        "validation_weight": d("0.200000"),
        "fallback_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchSourceScrapingReadinessConfig(**values)


def source(
    index: int,
    *,
    private_source_id: str | None = None,
    access_policy: str = "allowed",
    automated_collection_allowed: bool = True,
    credential_required: bool = False,
    credential_access_approved: bool = False,
    structure_stability: str = "stable",
    cadence_seconds: Decimal = d("3600"),
    max_staleness_seconds: Decimal = d("7200"),
    validation_path: str = "independent_primary",
    fallback_path: str = "independent_alternate",
    fallback_tested: bool = True,
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceScrapingReadinessSource:
    return ResearchSourceScrapingReadinessSource(
        private_source_id=private_source_id or f"private-source-{index:03d}",
        access_policy=access_policy,
        automated_collection_allowed=automated_collection_allowed,
        credential_required=credential_required,
        credential_access_approved=credential_access_approved,
        structure_stability=structure_stability,
        cadence_seconds=cadence_seconds,
        max_staleness_seconds=max_staleness_seconds,
        validation_path=validation_path,
        fallback_path=fallback_path,
        fallback_tested=fallback_tested,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceScrapingReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceScrapingReadinessReport:
    return build_research_source_scraping_readiness_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_without_rows() -> None:
    readiness_report = report(())

    assert type(readiness_report) is ResearchSourceScrapingReadinessReport
    assert readiness_report.generated_at == GENERATED_AT
    assert readiness_report.config_version == "research-source-scraping-readiness-report-v0"
    assert readiness_report.source_count == d("0")
    assert readiness_report.pass_count == d("0")
    assert readiness_report.watch_count == d("0")
    assert readiness_report.blocked_count == d("0")
    assert readiness_report.average_readiness_score is None
    assert readiness_report.status == "blocked"
    assert readiness_report.rows == ()
    assert readiness_report.reason_codes == ("no_sources_to_assess",)
    assert readiness_report.reason_code_counts == (
        ResearchSourceScrapingReadinessReasonCodeCount(
            reason_code="no_sources_to_assess",
            count=d("1"),
        ),
    )
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True


def test_allowed_stable_fresh_validated_source_passes() -> None:
    readiness_report = report((source(1),))

    assert readiness_report.status == "pass"
    assert readiness_report.source_count == d("1")
    assert readiness_report.pass_count == d("1")
    assert readiness_report.watch_count == d("0")
    assert readiness_report.blocked_count == d("0")
    assert readiness_report.average_readiness_score == d("1.000000")
    assert readiness_report.reason_codes == ("scraping_readiness_pass",)

    row = readiness_report.rows[0]
    assert type(row) is ResearchSourceScrapingReadinessRow
    assert row.source_index == d("1")
    assert row.allowability_score == d("1.000000")
    assert row.structure_score == d("1.000000")
    assert row.cadence_score == d("1.000000")
    assert row.validation_score == d("1.000000")
    assert row.fallback_score == d("1.000000")
    assert row.readiness_score == d("1.000000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "automation_allowed",
        "cadence_within_sla",
        "fallback_ready",
        "scraping_readiness_pass",
        "source_access_allowed",
        "source_shape_fixed",
        "validation_path_ready",
    )


def test_conditional_dynamic_untested_fallback_source_is_watch() -> None:
    readiness_report = report(
        (
            source(
                1,
                access_policy="conditional",
                credential_required=True,
                credential_access_approved=True,
                structure_stability="dynamic",
                cadence_seconds=d("10800"),
                max_staleness_seconds=d("7200"),
                validation_path="manual_review",
                fallback_path="cached_snapshot",
                fallback_tested=False,
                reason_codes=("manual_reviewed",),
            ),
        ),
    )

    assert readiness_report.status == "watch"
    assert readiness_report.watch_count == d("1")
    assert readiness_report.average_readiness_score == d("0.530000")

    row = readiness_report.rows[0]
    assert row.status == "watch"
    assert row.allowability_score == d("0.700000")
    assert row.structure_score == d("0.500000")
    assert row.cadence_score == d("0.500000")
    assert row.validation_score == d("0.500000")
    assert row.fallback_score == d("0.300000")
    assert row.readiness_score == d("0.530000")
    assert row.reason_codes == (
        "automation_allowed",
        "cadence_watch",
        "credential_gate_ready",
        "fallback_untested",
        "fallback_watch",
        "input_manual_reviewed",
        "scraping_readiness_watch",
        "source_access_conditional",
        "source_shape_watch",
        "validation_path_watch",
    )


def test_disallowed_source_with_no_validation_or_fallback_is_blocked() -> None:
    readiness_report = report(
        (
            source(
                1,
                access_policy="disallowed",
                automated_collection_allowed=False,
                structure_stability="unstable",
                cadence_seconds=d("20000"),
                max_staleness_seconds=d("7200"),
                validation_path="none",
                fallback_path="none",
                fallback_tested=False,
            ),
        ),
    )

    row = readiness_report.rows[0]
    assert readiness_report.status == "blocked"
    assert readiness_report.blocked_count == d("1")
    assert readiness_report.average_readiness_score == d("0.025000")
    assert row.status == "blocked"
    assert row.allowability_score == d("0.000000")
    assert row.structure_score == d("0.100000")
    assert row.cadence_score == d("0.000000")
    assert row.validation_score == d("0.000000")
    assert row.fallback_score == d("0.000000")
    assert row.readiness_score == d("0.025000")
    assert row.reason_codes == (
        "automation_not_allowed",
        "cadence_blocked",
        "fallback_missing",
        "scraping_readiness_blocked",
        "source_access_blocked",
        "source_shape_unfixed",
        "validation_path_missing",
    )


def test_rows_are_sorted_counts_are_deterministic_and_payload_uses_no_float_values() -> None:
    readiness_report = report(
        (
            source(2, private_source_id="z-private"),
            source(
                1,
                private_source_id="a-private",
                access_policy="conditional",
                credential_required=True,
                credential_access_approved=True,
                structure_stability="dynamic",
                validation_path="manual_review",
                fallback_path="cached_snapshot",
                fallback_tested=False,
            ),
        ),
    )
    payload = research_source_scraping_readiness_report_payload(readiness_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.source_index for row in readiness_report.rows) == (d("1"), d("2"))
    assert readiness_report.status == "watch"
    assert readiness_report.pass_count == d("1")
    assert readiness_report.watch_count == d("1")
    assert readiness_report.blocked_count == d("0")
    assert readiness_report.average_readiness_score == d("0.815000")
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["readiness_score"] == "0.630000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_public_payload_omits_private_locator_material_and_rejects_unsafe_codes() -> None:
    private_locator = "https://private.example/query?token=abc123&table=markets"
    readiness_report = report(
        (
            source(
                1,
                private_source_id=private_locator,
                reason_codes=("operator_checked",),
            ),
        ),
    )

    payload = research_source_scraping_readiness_report_payload(readiness_report)
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert private_locator.lower() not in encoded
    for unsafe_fragment in ("url", "text", "ref", "dsn", "table", "token", "https://"):
        assert unsafe_fragment not in encoded
    with pytest.raises(ValueError, match="source material"):
        source(2, reason_codes=("token_found",))
    with pytest.raises(ValueError, match="source material"):
        source(3, reason_codes=("raw_text_found",))


def test_validation_rejects_bad_types_enums_duplicates_and_flags() -> None:
    with pytest.raises(ValueError, match="allowability_weight"):
        config(allowability_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_readiness_score"):
        config(pass_readiness_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fallback_weight"):
        config(fallback_weight=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((source(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((source(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="sources"):
        report(("not-a-source",))
    with pytest.raises(ValueError, match="unique"):
        report((source(1, private_source_id="dup"), source(2, private_source_id="dup")))
    with pytest.raises(ValueError, match="access_policy"):
        source(1, access_policy="unknown")
    with pytest.raises(ValueError, match="automated_collection_allowed"):
        source(1, automated_collection_allowed=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cadence_seconds"):
        source(1, cadence_seconds=d("0"))
    with pytest.raises(ValueError, match="cadence_seconds"):
        source(1, cadence_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="validation_path"):
        source(1, validation_path="same_page")
    with pytest.raises(ValueError, match="fallback_tested"):
        source(1, fallback_path="none", fallback_tested=True)
    with pytest.raises(ValueError, match="paper_only"):
        replace(source(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    readiness_report = report((source(1),))

    with pytest.raises(FrozenInstanceError):
        readiness_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness_report.rows[0].readiness_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="pass_count"):
        replace(readiness_report, pass_count=d("0"))
    with pytest.raises(ValueError, match="rows"):
        replace(readiness_report, rows=(readiness_report.rows[0], readiness_report.rows[0]))
    with pytest.raises(ValueError, match="source_index"):
        replace(readiness_report.rows[0], source_index=d("1.5"))


def test_owned_module_has_no_collection_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_scraping_readiness_report.py"
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
        ".get(",
        ".post(",
    )

    assert all(term not in source_code for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for key, item in value.items():
            values.extend(_walk_payload_values(key))
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
