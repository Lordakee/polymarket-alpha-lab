from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_source_fact_claim_lineage_report as api
from polymarket_alpha_lab.research_source_fact_claim_lineage_report import (
    ResearchSourceFactClaimLineageConfig,
    ResearchSourceFactClaimLineageEvidence,
    ResearchSourceFactClaimLineageReport,
    ResearchSourceFactClaimLineageRow,
    build_research_source_fact_claim_lineage_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_fact_claim_lineage_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def _evidence(
    *,
    lineage_key: str = "lineage_a",
    claim_key: str = "claim_a",
    observed_at: datetime = NOW,
    source_authority_score: Decimal = Decimal("0.900000"),
    corroboration_hops: Decimal = Decimal("2.000000"),
    contradiction_severity: Decimal = Decimal("0.000000"),
    extraction_confidence: Decimal = Decimal("0.850000"),
    manual_verification_coverage: Decimal = Decimal("0.800000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceFactClaimLineageEvidence:
    return ResearchSourceFactClaimLineageEvidence(
        lineage_key=lineage_key,
        claim_key=claim_key,
        observed_at=observed_at,
        source_authority_score=source_authority_score,
        corroboration_hops=corroboration_hops,
        contradiction_severity=contradiction_severity,
        extraction_confidence=extraction_confidence,
        manual_verification_coverage=manual_verification_coverage,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    evidence: tuple[ResearchSourceFactClaimLineageEvidence, ...],
    *,
    config: ResearchSourceFactClaimLineageConfig | None = None,
) -> ResearchSourceFactClaimLineageReport:
    return build_research_source_fact_claim_lineage_report(
        evidence,
        generated_at=NOW,
        config=config,
    )


def test_lineage_report_passes_and_tracks_all_quality_dimensions() -> None:
    report = _report(
        (
            _evidence(source_authority_score=Decimal("0.900000")),
            _evidence(source_authority_score=Decimal("0.800000")),
        ),
    )

    row = report.rows[0]
    assert report.report_status == "pass"
    assert report.claim_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert row.source_count == Decimal("2.000000")
    assert row.average_source_authority_score == Decimal("0.850000")
    assert row.freshness_score == Decimal("1.000000")
    assert row.max_corroboration_hops == Decimal("2.000000")
    assert row.corroboration_hop_score == Decimal("1.000000")
    assert row.max_contradiction_severity == Decimal("0.000000")
    assert row.average_extraction_confidence == Decimal("0.850000")
    assert row.manual_verification_coverage == Decimal("0.800000")
    assert row.lineage_score == Decimal("0.916667")
    assert row.lineage_status == "pass"
    assert row.reason_codes == ("fact_claim_lineage_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_watch_and_block_statuses_reflect_manual_coverage_and_contradictions() -> None:
    report = _report(
        (
            _evidence(
                lineage_key="lineage_watch",
                claim_key="claim_watch",
                manual_verification_coverage=Decimal("0.200000"),
            ),
            _evidence(
                lineage_key="lineage_block",
                claim_key="claim_block",
                contradiction_severity=Decimal("0.800000"),
            ),
        ),
    )

    rows = {row.claim_key: row for row in report.rows}
    assert report.report_status == "block"
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert rows["claim_watch"].lineage_status == "watch"
    assert "manual_verification_coverage_watch" in rows["claim_watch"].reason_codes
    assert rows["claim_block"].lineage_status == "block"
    assert "contradiction_severity_block" in rows["claim_block"].reason_codes


def test_payload_is_deterministic_json_decimal_stringed_and_digest_validated() -> None:
    report = _report(
        (
            _evidence(lineage_key="lineage_b", claim_key="claim_b"),
            _evidence(lineage_key="lineage_a", claim_key="claim_a"),
        ),
    )

    payload = report.payload
    canonical_one = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    canonical_two = json.dumps(report.payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    assert canonical_one == canonical_two
    assert payload["claim_count"] == "2.000000"
    assert payload["rows"][0]["lineage_key"] == "lineage_a"
    assert payload["rows"][0]["lineage_score"] == "0.925000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_decimal_inputs_are_exact_raw_bounded_signed_zero_safe_and_context_fixed() -> None:
    with pytest.raises(ValueError, match="source_authority_score must be exactly Decimal"):
        _evidence(source_authority_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="contradiction_severity must be finite"):
        _evidence(contradiction_severity=Decimal("NaN"))

    with pytest.raises(ValueError, match="source_authority_score must be between zero and one"):
        _evidence(source_authority_score=Decimal("1.0000004"))

    with pytest.raises(ValueError, match="corroboration_hops must be nonnegative"):
        _evidence(corroboration_hops=Decimal("-0.0000004"))

    signed_zero = _report((_evidence(contradiction_severity=Decimal("-0")),))
    assert signed_zero.rows[0].max_contradiction_severity == Decimal("0.000000")
    assert signed_zero.payload["rows"][0]["max_contradiction_severity"] == "0.000000"

    with localcontext() as context:
        context.prec = 4
        low_context = _report(
            (
                _evidence(source_authority_score=Decimal("0.900000")),
                _evidence(source_authority_score=Decimal("0.800000")),
            ),
        )
    assert low_context.rows[0].average_source_authority_score == Decimal("0.850000")
    assert low_context.rows[0].lineage_score == Decimal("0.916667")


def test_dataclasses_are_frozen_exact_type_final_and_hard_flags_are_enforced() -> None:
    report = _report((_evidence(),))
    public_classes = (
        ResearchSourceFactClaimLineageConfig,
        ResearchSourceFactClaimLineageEvidence,
        ResearchSourceFactClaimLineageRow,
        api.ResearchSourceFactClaimLineageReasonCodeCount,
        ResearchSourceFactClaimLineageReport,
    )
    for public_class in public_classes:
        assert public_class.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadRow(ResearchSourceFactClaimLineageRow):
            pass

    with pytest.raises(TypeError):

        class BadReport(ResearchSourceFactClaimLineageReport):
            pass

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        _evidence(observed_at=_DatetimeSubclass(2026, 1, 1, tzinfo=UTC))

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceFactClaimLineageConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _evidence(report_only=False)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_public_schemas_reason_counts_and_exports_are_exact() -> None:
    report = _report(
        (
            _evidence(lineage_key="lineage_pass", claim_key="claim_pass"),
            _evidence(
                lineage_key="lineage_block",
                claim_key="claim_block",
                contradiction_severity=Decimal("0.800000"),
            ),
        ),
    )

    assert api.PUBLIC_CONFIG_PAYLOAD_FIELDS == (
        "config_version",
        "max_fresh_age_seconds",
        "min_source_authority_score",
        "min_freshness_score",
        "min_corroboration_hops",
        "full_corroboration_hops",
        "watch_contradiction_severity",
        "block_contradiction_severity",
        "min_extraction_confidence",
        "min_manual_verification_coverage",
        "min_lineage_score",
        "block_lineage_score",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    )
    assert api.PUBLIC_ROW_PAYLOAD_FIELDS == (
        "lineage_key",
        "claim_key",
        "source_count",
        "average_source_authority_score",
        "freshness_score",
        "max_corroboration_hops",
        "corroboration_hop_score",
        "max_contradiction_severity",
        "average_extraction_confidence",
        "manual_verification_coverage",
        "lineage_score",
        "lineage_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    )
    assert api.PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS == (
        "reason_code",
        "row_count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    )
    assert api.PUBLIC_REPORT_PAYLOAD_FIELDS == (
        "config_version",
        "config",
        "generated_at",
        "report_status",
        "claim_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_lineage_score",
        "max_contradiction_severity",
        "min_manual_verification_coverage",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    )

    payload = report.payload
    assert list(payload) == list(api.PUBLIC_REPORT_PAYLOAD_FIELDS)
    assert list(payload["config"]) == list(api.PUBLIC_CONFIG_PAYLOAD_FIELDS)
    assert list(payload["rows"][0]) == list(api.PUBLIC_ROW_PAYLOAD_FIELDS)
    assert list(payload["reason_code_counts"][0]) == list(
        api.PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS,
    )
    assert payload["reason_codes"] == [
        "contradiction_severity_block",
        "fact_claim_lineage_pass",
    ]
    assert payload["reason_code_counts"] == [
        {
            "reason_code": "contradiction_severity_block",
            "row_count": "1.000000",
            "row_ratio": "0.500000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "derived_validation_digest": report.reason_code_counts[0].derived_validation_digest,
        },
        {
            "reason_code": "fact_claim_lineage_pass",
            "row_count": "1.000000",
            "row_ratio": "0.500000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "derived_validation_digest": report.reason_code_counts[1].derived_validation_digest,
        },
    ]
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert api.research_source_fact_claim_lineage_report_digest(report) == (
        report.derived_validation_digest
    )
    assert api.validate_research_source_fact_claim_lineage_public_payload(payload)
    assert api.research_source_fact_claim_lineage_report_payload(payload) == payload

    reordered = {
        "generated_at": payload["generated_at"],
        **{key: value for key, value in payload.items() if key != "generated_at"},
    }
    with pytest.raises(ValueError, match="field order"):
        api.research_source_fact_claim_lineage_report_payload(reordered)


def test_payload_access_rejects_object_setattr_tampering_and_nested_reconstruction() -> None:
    report = _report((_evidence(),))
    object.__setattr__(report, "pass_count", Decimal("0.000000"))
    with pytest.raises(ValueError, match="pass_count|derived_validation_digest"):
        report.payload

    nested = _report((_evidence(),))
    object.__setattr__(nested.rows[0], "lineage_status", "watch")
    with pytest.raises(ValueError, match="derived_validation_digest|lineage_status"):
        nested.payload

    replaced = _report((_evidence(),))
    object.__setattr__(replaced, "rows", (replaced.rows[0].payload,))
    with pytest.raises(ValueError, match="row|rows"):
        replaced.payload


def test_resigned_payload_rederives_all_status_reason_score_count_order_and_aggregates() -> None:
    original = _report(
        (
            _evidence(lineage_key="lineage_pass", claim_key="claim_pass"),
            _evidence(
                lineage_key="lineage_block",
                claim_key="claim_block",
                contradiction_severity=Decimal("0.800000"),
            ),
        ),
    ).payload

    resigned = json.loads(json.dumps(original))
    block_row = resigned["rows"][0]
    assert block_row["claim_key"] == "claim_block"
    block_row["lineage_status"] = "pass"
    block_row["reason_codes"] = ["fact_claim_lineage_pass"]
    block_row["derived_validation_digest"] = _test_digest(
        "research_source_fact_claim_lineage_row",
        block_row,
        api.PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )

    resigned["report_status"] = "pass"
    resigned["pass_count"] = "2.000000"
    resigned["block_count"] = "0.000000"
    resigned["reason_codes"] = ["fact_claim_lineage_pass"]
    resigned["reason_code_counts"] = [
        {
            "reason_code": "fact_claim_lineage_pass",
            "row_count": "2.000000",
            "row_ratio": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    resigned["reason_code_counts"][0]["derived_validation_digest"] = _test_digest(
        "research_source_fact_claim_lineage_reason_code_count",
        resigned["reason_code_counts"][0],
        api.PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )
    resigned["derived_validation_digest"] = _test_digest(
        "research_source_fact_claim_lineage_report",
        resigned,
        api.PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )

    with pytest.raises(ValueError, match="lineage_status|reason_codes|block_count"):
        api.research_source_fact_claim_lineage_report_payload(resigned)
    assert not api.validate_research_source_fact_claim_lineage_public_payload(resigned)


def test_public_payload_rejects_raw_candidate_market_url_text_id_token_and_live_surfaces() -> None:
    unsafe_values = (
        "candidate_123",
        "market_123",
        "slug_abc",
        "question_abc",
        "https://example.test/item",
        "example.test",
        "raw_text",
        "dsn_value",
        "table_value",
        "token_value",
        "550e8400-e29b-41d4-a716-446655440000",
        "0xdeaddeaddeaddeaddeaddeaddeaddeaddeaddead",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.c2lnbmF0dXJl",
        "wallet_value",
        "order_value",
        "trade_value",
        "live_value",
    )
    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            _evidence(lineage_key=value)

    report = _report((_evidence(),))
    payload_blob = json.dumps(report.payload, sort_keys=True)
    for unsafe in unsafe_values:
        assert unsafe not in payload_blob


def test_public_surface_exposes_no_io_or_market_sensitive_fields() -> None:
    unsafe_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchSourceFactClaimLineageConfig,
        ResearchSourceFactClaimLineageEvidence,
        ResearchSourceFactClaimLineageRow,
        ResearchSourceFactClaimLineageReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "web3",
            "ccxt",
            "subprocess",
            "os",
        },
    )


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _test_digest(
    label: str,
    payload: dict[str, object],
    field_names: tuple[str, ...],
) -> str:
    canonical = json.dumps(
        {field_name: payload[field_name] for field_name in field_names},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(f"{label}|{canonical}".encode("utf-8")).hexdigest()
