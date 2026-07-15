from __future__ import annotations

import ast
import hashlib
import importlib
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, Inexact, ROUND_DOWN, localcontext
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_source_scraping_authority_shadow_gap_report"
)
GENERATED_AT = datetime(2026, 7, 9, 9, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "freshness_watch_age_seconds": d("3600.000000"),
        "freshness_block_age_seconds": d("10800.000000"),
        "authority_gap_watch_score": d("0.250000"),
        "authority_gap_block_score": d("0.500000"),
        "scraping_count_gap_watch_score": d("0.400000"),
        "scraping_count_gap_block_score": d("0.700000"),
        "conflict_watch_ratio": d("0.400000"),
        "conflict_block_ratio": d("0.750000"),
        "fallback_watch_ratio": d("0.400000"),
        "fallback_block_ratio": d("0.750000"),
        "shadow_gap_watch_score": d("0.350000"),
        "shadow_gap_block_score": d("0.650000"),
    }
    values.update(overrides)
    return module.ResearchSourceScrapingAuthorityShadowGapConfig(**values)


def shadow_item(
    public_shadow_key: str,
    authority_bucket: str,
    *,
    scraped_authority_score: Decimal = d("0.900000"),
    shadow_authority_score: Decimal = d("0.950000"),
    scraped_authority_evidence_count: Decimal = d("3.000000"),
    shadow_authority_evidence_count: Decimal = d("3.000000"),
    freshest_authority_scrape_age_seconds: Decimal = d("900.000000"),
    authority_conflict_ratio: Decimal = d("0.050000"),
    fallback_only_ratio: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScrapingAuthorityShadowGapInput(
        public_shadow_key=public_shadow_key,
        authority_bucket=authority_bucket,
        scraped_authority_score=scraped_authority_score,
        shadow_authority_score=shadow_authority_score,
        scraped_authority_evidence_count=scraped_authority_evidence_count,
        shadow_authority_evidence_count=shadow_authority_evidence_count,
        freshest_authority_scrape_age_seconds=freshest_authority_scrape_age_seconds,
        authority_conflict_ratio=authority_conflict_ratio,
        fallback_only_ratio=fallback_only_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_scraping_authority_shadow_gap_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resigned_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = deepcopy(payload)
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def test_shadow_gap_report_scores_and_ranks_pass_watch_block_rows() -> None:
    module = api()
    report = build_report(
        shadow_item("shadow-sports", "sports.soccer"),
        shadow_item(
            "shadow-macro",
            "finance.macro",
            scraped_authority_score=d("0.600000"),
            shadow_authority_score=d("0.900000"),
            scraped_authority_evidence_count=d("2.000000"),
            shadow_authority_evidence_count=d("3.000000"),
            freshest_authority_scrape_age_seconds=d("5400.000000"),
            authority_conflict_ratio=d("0.450000"),
            fallback_only_ratio=d("0.200000"),
        ),
        shadow_item(
            "shadow-politics",
            "politics",
            scraped_authority_score=d("0.200000"),
            shadow_authority_score=d("0.900000"),
            scraped_authority_evidence_count=d("1.000000"),
            shadow_authority_evidence_count=d("5.000000"),
            freshest_authority_scrape_age_seconds=d("12000.000000"),
            authority_conflict_ratio=d("0.800000"),
            fallback_only_ratio=d("0.900000"),
        ),
    )

    assert type(report) is module.ResearchSourceScrapingAuthorityShadowGapReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.shadow_item_count == d("3.000000")
    assert report.pass_shadow_item_count == d("1.000000")
    assert report.watch_shadow_item_count == d("1.000000")
    assert report.block_shadow_item_count == d("1.000000")
    assert report.authority_shadow_gap_count == d("2.000000")
    assert report.scraping_count_gap_count == d("1.000000")
    assert report.stale_scrape_count == d("2.000000")
    assert report.conflict_pressure_count == d("2.000000")
    assert report.fallback_dependency_count == d("1.000000")
    assert report.highest_shadow_gap_score == d("0.825000")
    assert report.highest_authority_shadow_gap_score == d("0.700000")
    assert report.highest_scraping_count_gap_score == d("0.800000")
    assert report.oldest_authority_scrape_age_seconds == d("12000.000000")
    assert report.average_shadow_gap_score == d("0.406111")
    assert tuple(row.public_shadow_key for row in report.rows) == (
        "shadow-politics",
        "shadow-macro",
        "shadow-sports",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.shadow_gap_score for row in report.rows) == (
        d("0.825000"),
        d("0.354167"),
        d("0.039167"),
    )

    blocked = report.rows[0]
    assert blocked.authority_shadow_gap_score == d("0.700000")
    assert blocked.scraping_count_gap_score == d("0.800000")
    assert blocked.freshness_pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "research_source_scraping_authority_shadow_gap_authority_block",
        "research_source_scraping_authority_shadow_gap_count_block",
        "research_source_scraping_authority_shadow_gap_stale_block",
        "research_source_scraping_authority_shadow_gap_conflict_block",
        "research_source_scraping_authority_shadow_gap_fallback_block",
        "research_source_scraping_authority_shadow_gap_score_block",
    )
    assert report.reason_codes == (
        "research_source_scraping_authority_shadow_gap_authority_block",
        "research_source_scraping_authority_shadow_gap_count_block",
        "research_source_scraping_authority_shadow_gap_stale_block",
        "research_source_scraping_authority_shadow_gap_conflict_block",
        "research_source_scraping_authority_shadow_gap_fallback_block",
        "research_source_scraping_authority_shadow_gap_score_block",
        "research_source_scraping_authority_shadow_gap_authority_watch",
        "research_source_scraping_authority_shadow_gap_stale_watch",
        "research_source_scraping_authority_shadow_gap_conflict_watch",
        "research_source_scraping_authority_shadow_gap_score_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_input_returns_pass_readonly_report() -> None:
    report = build_report()

    assert report.status == "pass"
    assert report.shadow_item_count == d("0.000000")
    assert report.highest_shadow_gap_score == d("0.000000")
    assert report.average_shadow_gap_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_source_scraping_authority_shadow_gap_empty",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_public_payload_is_deterministic_decimal_only_safe_and_digest_checked() -> None:
    module = api()
    rows = (
        shadow_item(
            "shadow-politics",
            "politics",
            scraped_authority_score=d("0.200000"),
            shadow_authority_score=d("0.900000"),
            scraped_authority_evidence_count=d("1.000000"),
            shadow_authority_evidence_count=d("5.000000"),
            freshest_authority_scrape_age_seconds=d("12000.000000"),
            authority_conflict_ratio=d("0.800000"),
            fallback_only_ratio=d("0.900000"),
        ),
        shadow_item("shadow-sports", "sports.soccer"),
    )

    report_a = build_report(*rows)
    report_b = build_report(*reversed(rows))
    payload_a = module.research_source_scraping_authority_shadow_gap_report_payload(
        report_a,
    )
    payload_b = module.research_source_scraping_authority_shadow_gap_report_payload(
        report_b,
    )
    digest_a = module.research_source_scraping_authority_shadow_gap_report_digest(
        report_a,
    )

    assert payload_a == payload_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert len(payload_a["derived_validation_digest"]) == 64
    int(payload_a["derived_validation_digest"], 16)
    assert payload_a["generated_at"] == "2026-07-09T09:00:00+00:00"
    assert payload_a["rows"][0]["shadow_gap_score"] == "0.825000"
    assert payload_a["rows"][0]["scraping_count_gap_score"] == "0.800000"
    json.dumps(payload_a, sort_keys=True, allow_nan=False)
    assert_no_public_numeric_values(payload_a)
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_scraping_authority_shadow_gap_report_digest(report_a)
    module.validate_research_source_scraping_authority_shadow_gap_public_payload(
        payload_a,
    )

    tampered = dict(payload_a)
    tampered["watch_shadow_item_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_scraping_authority_shadow_gap_public_payload(
            tampered,
        )


def test_validation_rejects_bad_types_unsafe_labels_flags_and_manual_tampering() -> None:
    module = api()
    with pytest.raises(ValueError, match="freshness_watch_age_seconds must be a Decimal"):
        config(freshness_watch_age_seconds=3600)
    with pytest.raises(ValueError, match="authority_gap_watch_score must be a Decimal"):
        config(authority_gap_watch_score=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="scraped_authority_score must be a Decimal"):
        shadow_item("shadow-politics", "politics", scraped_authority_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="shadow_authority_evidence_count"):
        shadow_item(
            "shadow-politics",
            "politics",
            shadow_authority_evidence_count=d("1.500000"),
        )
    with pytest.raises(ValueError, match="public_shadow_key"):
        shadow_item("candidate-123", "politics")
    with pytest.raises(ValueError, match="authority_bucket"):
        shadow_item("shadow-politics", "https://example.invalid")
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        shadow_item("shadow-politics", "politics", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        shadow_item("shadow-politics", "politics", readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_scraping_authority_shadow_gap_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 9, 0),
        )

    report = build_report(shadow_item("shadow-politics", "politics"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="shadow_gap_score"):
        replace(report.rows[0], shadow_gap_score=d("0.990000"))

    payload = module.research_source_scraping_authority_shadow_gap_report_payload(report)
    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"safe": "https://example.invalid"},
        {"safe": "wallet token"},
        {"table_name": "public_summary"},
        {"safe": "live order trade recommendation"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_source_scraping_authority_shadow_gap_public_payload(
                {
                    **payload,
                    **unsafe_payload,
                    "derived_validation_digest": payload["derived_validation_digest"],
                },
            )


def test_decimal_boundaries_use_raw_values_fixed_context_and_canonical_zero() -> None:
    with pytest.raises(ValueError, match="scraped_authority_score.*six decimal places"):
        shadow_item(
            "shadow-raw-precision",
            "politics",
            scraped_authority_score=d("0.1234564"),
        )
    with pytest.raises(
        ValueError,
        match="authority_gap_watch_score.*six decimal places",
    ):
        config(authority_gap_watch_score=d("0.2500004"))
    with pytest.raises(ValueError, match="scraped_authority_score.*between zero and one"):
        shadow_item(
            "shadow-raw-upper-bound",
            "politics",
            scraped_authority_score=d("1.0000004"),
        )
    with pytest.raises(
        ValueError,
        match="shadow_authority_evidence_count.*whole Decimal",
    ):
        shadow_item(
            "shadow-raw-whole-bound",
            "politics",
            shadow_authority_evidence_count=d("1.0000004"),
        )

    for nonfinite in (d("NaN"), d("Infinity"), d("-Infinity")):
        with pytest.raises(ValueError, match="scraped_authority_score must be finite"):
            shadow_item(
                "shadow-nonfinite",
                "politics",
                scraped_authority_score=nonfinite,
            )

    with localcontext(Context(prec=2, rounding=ROUND_DOWN)) as ambient:
        ambient.traps[Inexact] = True
        report = build_report(
            shadow_item(
                "shadow-fixed-context",
                "politics",
                scraped_authority_score=d("0.123456"),
                shadow_authority_score=d("0.987654"),
                scraped_authority_evidence_count=d("1.000000"),
                shadow_authority_evidence_count=d("3.000000"),
                freshest_authority_scrape_age_seconds=d("1000.000000"),
                authority_conflict_ratio=d("0.333333"),
                fallback_only_ratio=d("0.222222"),
            ),
        )

    assert report.rows[0].authority_shadow_gap_score == d("0.864198")
    assert report.rows[0].scraping_count_gap_score == d("0.666667")
    assert report.rows[0].freshness_pressure_score == d("0.092593")
    assert report.rows[0].shadow_gap_score == d("0.494445")

    zero_report = build_report(
        shadow_item(
            "shadow-canonical-zero",
            "politics",
            scraped_authority_score=d("-0"),
            shadow_authority_score=d("-0"),
            scraped_authority_evidence_count=d("-0"),
            shadow_authority_evidence_count=d("-0"),
            freshest_authority_scrape_age_seconds=d("-0"),
            authority_conflict_ratio=d("-0"),
            fallback_only_ratio=d("-0"),
        ),
    )
    zero_row = zero_report.rows[0]
    for value in (
        zero_row.scraped_authority_score,
        zero_row.shadow_authority_score,
        zero_row.scraped_authority_evidence_count,
        zero_row.shadow_authority_evidence_count,
        zero_row.freshest_authority_scrape_age_seconds,
        zero_row.authority_conflict_ratio,
        zero_row.fallback_only_ratio,
        zero_row.authority_shadow_gap_score,
        zero_row.scraping_count_gap_score,
        zero_row.freshness_pressure_score,
        zero_row.shadow_gap_score,
    ):
        assert value == d("0.000000")
        assert value.is_signed() is False
    assert "-0.000000" not in json.dumps(
        api().research_source_scraping_authority_shadow_gap_report_payload(
            zero_report,
        ),
        sort_keys=True,
    )


def test_private_source_labels_are_rejected_before_public_reporting() -> None:
    for private_label in (
        "shadow-private-source",
        "shadow-secret-source",
        "shadow-api_key-prod",
        "shadow-credential-ref",
    ):
        with pytest.raises(ValueError, match="public_shadow_key contains unsafe text"):
            shadow_item(private_label, "politics")


def test_public_payload_uses_exact_canonical_schema_and_sha256() -> None:
    module = api()
    report = build_report(shadow_item("shadow-politics", "politics"))
    payload = module.research_source_scraping_authority_shadow_gap_report_payload(report)

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "derivation_config",
        "shadow_item_count",
        "pass_shadow_item_count",
        "watch_shadow_item_count",
        "block_shadow_item_count",
        "authority_shadow_gap_count",
        "scraping_count_gap_count",
        "stale_scrape_count",
        "conflict_pressure_count",
        "fallback_dependency_count",
        "highest_shadow_gap_score",
        "highest_authority_shadow_gap_score",
        "highest_scraping_count_gap_score",
        "oldest_authority_scrape_age_seconds",
        "average_shadow_gap_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["derivation_config"]) == (
        "config_version",
        "freshness_watch_age_seconds",
        "freshness_block_age_seconds",
        "authority_gap_watch_score",
        "authority_gap_block_score",
        "scraping_count_gap_watch_score",
        "scraping_count_gap_block_score",
        "conflict_watch_ratio",
        "conflict_block_ratio",
        "fallback_watch_ratio",
        "fallback_block_ratio",
        "shadow_gap_watch_score",
        "shadow_gap_block_score",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["reason_code_counts"][0]) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["rows"][0]) == (
        "public_shadow_key",
        "authority_bucket",
        "scraped_authority_score",
        "shadow_authority_score",
        "scraped_authority_evidence_count",
        "shadow_authority_evidence_count",
        "freshest_authority_scrape_age_seconds",
        "authority_conflict_ratio",
        "fallback_only_ratio",
        "authority_shadow_gap_score",
        "scraping_count_gap_score",
        "freshness_pressure_score",
        "shadow_gap_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == payload[
        "derived_validation_digest"
    ].lower()
    int(payload["derived_validation_digest"], 16)

    for mutate in (
        lambda value: value.update({"unexpected": "field"}),
        lambda value: value["rows"][0].pop("authority_bucket"),
        lambda value: value.update({"shadow_item_count": "1"}),
        lambda value: value.update({"shadow_item_count": "-0.000000"}),
    ):
        malformed = deepcopy(payload)
        mutate(malformed)
        malformed = resigned_payload(malformed)
        with pytest.raises(ValueError, match="canonical schema|canonical Decimal"):
            module.validate_research_source_scraping_authority_shadow_gap_public_payload(
                malformed,
            )


def test_resigned_payload_recomputes_complete_derived_state() -> None:
    module = api()
    report = build_report(
        shadow_item(
            "shadow-politics",
            "politics",
            scraped_authority_score=d("0.200000"),
            shadow_authority_score=d("0.900000"),
            scraped_authority_evidence_count=d("1.000000"),
            shadow_authority_evidence_count=d("5.000000"),
            freshest_authority_scrape_age_seconds=d("12000.000000"),
            authority_conflict_ratio=d("0.800000"),
            fallback_only_ratio=d("0.900000"),
        ),
    )
    payload = module.research_source_scraping_authority_shadow_gap_report_payload(report)

    tampered_count = deepcopy(payload)
    tampered_count["block_shadow_item_count"] = "0.000000"
    with pytest.raises(ValueError, match="block_shadow_item_count"):
        module.validate_research_source_scraping_authority_shadow_gap_public_payload(
            resigned_payload(tampered_count),
        )

    tampered_row = deepcopy(payload)
    tampered_row["rows"][0]["authority_shadow_gap_score"] = "0.600000"
    with pytest.raises(ValueError, match="authority_shadow_gap_score"):
        module.validate_research_source_scraping_authority_shadow_gap_public_payload(
            resigned_payload(tampered_row),
        )

    tampered_freshness_chain = deepcopy(payload)
    tampered_freshness_chain["rows"][0]["freshness_pressure_score"] = "0.500000"
    tampered_freshness_chain["rows"][0]["shadow_gap_score"] = "0.725000"
    tampered_freshness_chain["highest_shadow_gap_score"] = "0.725000"
    tampered_freshness_chain["average_shadow_gap_score"] = "0.725000"
    with pytest.raises(ValueError, match="freshness_pressure_score"):
        module.validate_research_source_scraping_authority_shadow_gap_public_payload(
            resigned_payload(tampered_freshness_chain),
        )


def test_rows_use_stable_score_bucket_and_public_key_tie_breaks() -> None:
    module = api()
    rows = (
        shadow_item("shadow-z", "politics"),
        shadow_item("shadow-a", "sports.soccer"),
        shadow_item("shadow-a", "politics"),
    )
    report_a = build_report(*rows)
    report_b = build_report(*reversed(rows))

    assert tuple(
        (row.authority_bucket, row.public_shadow_key) for row in report_a.rows
    ) == (
        ("politics", "shadow-a"),
        ("politics", "shadow-z"),
        ("sports.soccer", "shadow-a"),
    )
    assert (
        module.research_source_scraping_authority_shadow_gap_report_payload(report_a)
        == module.research_source_scraping_authority_shadow_gap_report_payload(report_b)
    )


def test_rejects_resigned_payloads_with_noncanonical_mapping_key_order() -> None:
    module = api()
    payload = module.research_source_scraping_authority_shadow_gap_report_payload(
        build_report(shadow_item("shadow-politics", "politics")),
    )
    for reorder in (
        lambda value: dict(reversed(tuple(value.items()))),
        lambda value: {
            **value,
            "derivation_config": dict(
                reversed(tuple(value["derivation_config"].items())),
            ),
        },
        lambda value: {
            **value,
            "reason_code_counts": [
                dict(reversed(tuple(value["reason_code_counts"][0].items()))),
            ],
        },
        lambda value: {
            **value,
            "rows": [dict(reversed(tuple(value["rows"][0].items())))],
        },
    ):
        with pytest.raises(ValueError, match="canonical schema"):
            module.validate_research_source_scraping_authority_shadow_gap_public_payload(
                resigned_payload(reorder(deepcopy(payload))),
            )


def test_revalidates_object_setattr_mutated_boundary_objects() -> None:
    module = api()

    mutated_config = config()
    object.__setattr__(
        mutated_config,
        "freshness_block_age_seconds",
        d("0.000000"),
    )
    with pytest.raises(ValueError, match="freshness_block_age_seconds must be positive"):
        build_report(shadow_item("shadow-config", "politics"), cfg=mutated_config)

    mutated_input = shadow_item("shadow-input", "politics")
    object.__setattr__(
        mutated_input,
        "authority_conflict_ratio",
        _DecimalSubclass("0.050000"),
    )
    with pytest.raises(ValueError, match="authority_conflict_ratio must be a Decimal"):
        build_report(mutated_input)

    report = build_report(shadow_item("shadow-row", "politics"))
    mutated_row = report.rows[0]
    object.__setattr__(mutated_row, "public_shadow_key", "wallet-shadow")
    with pytest.raises(ValueError, match="public_shadow_key contains unsafe text"):
        replace(report, rows=(mutated_row,), derived_validation_digest="")

    mutated_reason_count = report.reason_code_counts[0]
    object.__setattr__(
        mutated_reason_count,
        "count",
        _DecimalSubclass("1.000000"),
    )
    with pytest.raises(ValueError, match="count must be a Decimal"):
        replace(
            report,
            reason_code_counts=(mutated_reason_count,),
            derived_validation_digest="",
        )


def test_resigned_payload_rederives_every_reported_status_reason_score_count_and_order() -> None:
    module = api()
    payload = module.research_source_scraping_authority_shadow_gap_report_payload(
        build_report(
            shadow_item("shadow-pass", "politics"),
            shadow_item(
                "shadow-block",
                "sports.soccer",
                scraped_authority_score=d("0.200000"),
                shadow_authority_score=d("0.900000"),
                scraped_authority_evidence_count=d("1.000000"),
                shadow_authority_evidence_count=d("5.000000"),
                freshest_authority_scrape_age_seconds=d("12000.000000"),
                authority_conflict_ratio=d("0.800000"),
                fallback_only_ratio=d("0.900000"),
            ),
        ),
    )

    def different_decimal(value: str) -> str:
        return "0.000001" if value == "0.000000" else "0.000000"

    aggregate_fields = (
        "shadow_item_count",
        "pass_shadow_item_count",
        "watch_shadow_item_count",
        "block_shadow_item_count",
        "authority_shadow_gap_count",
        "scraping_count_gap_count",
        "stale_scrape_count",
        "conflict_pressure_count",
        "fallback_dependency_count",
        "highest_shadow_gap_score",
        "highest_authority_shadow_gap_score",
        "highest_scraping_count_gap_score",
        "oldest_authority_scrape_age_seconds",
        "average_shadow_gap_score",
    )
    for field_name in aggregate_fields:
        tampered = deepcopy(payload)
        tampered[field_name] = different_decimal(tampered[field_name])
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_source_scraping_authority_shadow_gap_public_payload(
                resigned_payload(tampered),
            )

    for field_name in (
        "authority_shadow_gap_score",
        "scraping_count_gap_score",
        "freshness_pressure_score",
        "shadow_gap_score",
    ):
        tampered = deepcopy(payload)
        tampered["rows"][0][field_name] = different_decimal(
            tampered["rows"][0][field_name],
        )
        with pytest.raises(ValueError, match=f"{field_name}|shadow_gap_score"):
            module.validate_research_source_scraping_authority_shadow_gap_public_payload(
                resigned_payload(tampered),
            )

    for container, field_name, value in (
        (payload, "status", "pass"),
        (payload, "reason_codes", [module.CLEAR_REASON]),
        (payload["rows"][0], "status", "pass"),
        (payload["rows"][0], "reason_codes", [module.CLEAR_REASON]),
    ):
        tampered = deepcopy(payload)
        target = tampered if container is payload else tampered["rows"][0]
        target[field_name] = value
        with pytest.raises(ValueError, match="status|reason_codes"):
            module.validate_research_source_scraping_authority_shadow_gap_public_payload(
                resigned_payload(tampered),
            )

    tampered_count = deepcopy(payload)
    tampered_count["reason_code_counts"][0]["count"] = different_decimal(
        tampered_count["reason_code_counts"][0]["count"],
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.validate_research_source_scraping_authority_shadow_gap_public_payload(
            resigned_payload(tampered_count),
        )

    tampered_order = deepcopy(payload)
    tampered_order["rows"].reverse()
    with pytest.raises(ValueError, match="derived_validation_digest|canonical schema"):
        module.validate_research_source_scraping_authority_shadow_gap_public_payload(
            resigned_payload(tampered_order),
        )


def test_all_public_dataclasses_are_frozen_and_non_subclassable() -> None:
    module = api()
    report = build_report(shadow_item("shadow-politics", "politics"))
    public_values = (
        config(),
        shadow_item("shadow-politics", "politics"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for value in public_values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Derived{type(value).__name__}", (type(value),), {})


def test_exports_frozen_public_dataclasses_and_status_surface() -> None:
    module = api()
    report = build_report(shadow_item("shadow-politics", "politics"))

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_SCRAPING_AUTHORITY_SHADOW_GAP_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceScrapingAuthorityShadowGapConfig",
        "ResearchSourceScrapingAuthorityShadowGapInput",
        "ResearchSourceScrapingAuthorityShadowGapReasonCodeCount",
        "ResearchSourceScrapingAuthorityShadowGapReport",
        "ResearchSourceScrapingAuthorityShadowGapRow",
        "build_research_source_scraping_authority_shadow_gap_report",
        "research_source_scraping_authority_shadow_gap_report_digest",
        "research_source_scraping_authority_shadow_gap_report_payload",
        "validate_research_source_scraping_authority_shadow_gap_public_payload",
        "validate_research_source_scraping_authority_shadow_gap_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(shadow_item("shadow-politics", "politics"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().authority_gap_watch_score = d("0.100000")


def test_scope_is_pure_report_only_without_external_or_trading_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "scrapling",
        "agent_reach",
        "browser",
        "network",
        "source_url",
        "source_text",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "dsn",
        "table_name",
        "recommendation",
        "sizing",
        "authentication",
        "auth_token",
        "wallet",
        "account",
        "broker",
        "order_id",
        "trade_id",
        "private_key",
        "credential",
    ):
        assert forbidden not in lowered

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
                "submit_order",
                "place_order",
                "recommend",
                "size_position",
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
    unsafe_fields = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
    }
    report = build_report(shadow_item("shadow-politics", "politics"))
    field_names = {
        field.name
        for cls in (type(config()), type(shadow_item("shadow-politics", "politics")))
        for field in fields(cls)
    }
    field_names.update(field.name for field in fields(type(report)))
    field_names.update(field.name for field in fields(type(report.rows[0])))
    assert unsafe_fields.isdisjoint(field_names)


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
        assert type(value) is not Decimal


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
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
