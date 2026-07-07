from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from json import dumps
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_evidence_bundle_score"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def bundle_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "redacted_bundle_ref": "bundle-pass",
        "traceability_score": d("0.900000"),
        "staleness_score": d("0.100000"),
        "conflict_severity_score": d("0.100000"),
        "source_diversity_score": d("0.800000"),
        "revision_frequency_score": d("0.100000"),
        "reason_codes": ("research_filter_input",),
    }
    values.update(overrides)
    return module.ResearchEvidenceBundleScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.score_research_evidence_bundle(
        bundle_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_public_numbers_are_decimal_only(value: object) -> None:
    if value is None or type(value) in (bool, str):
        return
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numbers_are_decimal_only(getattr(value, field.name))
        return
    if isinstance(value, tuple):
        for item in value:
            assert_public_numbers_are_decimal_only(item)
        return
    assert type(value) is not int
    assert type(value) is not float


def assert_payload_has_no_int_or_float(value: Any) -> None:
    if type(value) is int or type(value) is float:
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_int_or_float(item)
    if isinstance(value, list):
        for item in value:
            assert_payload_has_no_int_or_float(item)


def test_pass_watch_and_block_bundle_scores_roll_up_to_report_status() -> None:
    module = api()

    passing = score()
    watching = score(
        bundle_input(
            redacted_bundle_ref="bundle-watch",
            traceability_score=d("0.600000"),
            staleness_score=d("0.400000"),
            conflict_severity_score=d("0.300000"),
            source_diversity_score=d("0.500000"),
            revision_frequency_score=d("0.450000"),
            reason_codes=(),
        ),
    )
    blocked = score(
        bundle_input(
            redacted_bundle_ref="bundle-block",
            traceability_score=d("0.400000"),
            staleness_score=d("0.800000"),
            conflict_severity_score=d("0.700000"),
            source_diversity_score=d("0.200000"),
            revision_frequency_score=d("0.800000"),
            reason_codes=(),
        ),
    )

    assert passing.evidence_bundle_quality_score == d("0.885000")
    assert passing.freshness_score == d("0.900000")
    assert passing.conflict_cleanliness_score == d("0.900000")
    assert passing.revision_stability_score == d("0.900000")
    assert passing.public_status == "pass"
    assert passing.reason_codes == (
        "research_filter_input",
        "research_evidence_bundle_score",
        "evidence_bundle_quality_pass",
        "traceability_pass",
        "staleness_pass",
        "conflict_severity_pass",
        "source_diversity_pass",
        "revision_frequency_pass",
    )

    assert watching.evidence_bundle_quality_score == d("0.605000")
    assert watching.public_status == "watch"
    assert "evidence_bundle_quality_watch" in watching.reason_codes
    assert "traceability_watch" in watching.reason_codes
    assert "staleness_watch" in watching.reason_codes
    assert "conflict_severity_watch" in watching.reason_codes
    assert "source_diversity_watch" in watching.reason_codes
    assert "revision_frequency_watch" in watching.reason_codes

    assert blocked.evidence_bundle_quality_score == d("0.285000")
    assert blocked.public_status == "block"
    assert "evidence_bundle_quality_block" in blocked.reason_codes
    assert "traceability_block" in blocked.reason_codes
    assert "staleness_block" in blocked.reason_codes
    assert "conflict_severity_block" in blocked.reason_codes
    assert "source_diversity_block" in blocked.reason_codes
    assert "revision_frequency_block" in blocked.reason_codes

    report = module.build_research_evidence_bundle_score_report(
        (watching.source_input, passing.source_input, blocked.source_input),
    )
    assert report.bundle_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_evidence_bundle_quality_score == d("0.591667")
    assert report.public_status == "block"
    assert tuple(row.redacted_bundle_ref for row in report.rows) == (
        "bundle-block",
        "bundle-pass",
        "bundle-watch",
    )


def test_decimal_fields_are_exact_decimal_only_and_dataclasses_are_frozen() -> None:
    module = api()
    subject = bundle_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.ResearchEvidenceBundleScoreConfig.__dataclass_params__.frozen
    assert module.ResearchEvidenceBundleScoreInput.__dataclass_params__.frozen
    assert module.ResearchEvidenceBundleScoreRow.__dataclass_params__.frozen
    assert module.ResearchEvidenceBundleScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.redacted_bundle_ref = "bundle-other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.public_status = "watch"  # type: ignore[misc]

    assert_public_numbers_are_decimal_only(subject)
    assert_public_numbers_are_decimal_only(result)

    with pytest.raises(ValueError, match="traceability_score must be a Decimal"):
        bundle_input(traceability_score=0.9)
    with pytest.raises(ValueError, match="staleness_score must be a Decimal"):
        bundle_input(staleness_score=1)
    with pytest.raises(ValueError, match="conflict_severity_score must be a Decimal"):
        bundle_input(conflict_severity_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="traceability_weight must be a Decimal"):
        module.ResearchEvidenceBundleScoreConfig(
            traceability_weight=DecimalSubclass("0.300000"),
        )
    with pytest.raises(ValueError, match="source_inputs must be a tuple"):
        module.build_research_evidence_bundle_score_report([subject])


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    module = api()

    unsafe_terms = (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_evidence_bundle_score_unsafe_payload(
                "unsafe-test",
                {term: "safe_public_value"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_evidence_bundle_score_unsafe_payload(
                "unsafe-test",
                {"safe_public_field": term},
            )

    with pytest.raises(ValueError, match="unsafe"):
        bundle_input(redacted_bundle_ref="market_slug")
    with pytest.raises(ValueError, match="unsafe"):
        bundle_input(reason_codes=("buy",))


def test_hard_flags_are_required_on_inputs_rows_reports_and_payloads() -> None:
    module = api()
    result = score()
    report = module.build_research_evidence_bundle_score_report((result.source_input,))

    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchEvidenceBundleScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        bundle_input(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)

    payload = module.research_evidence_bundle_score_payload(report)
    payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly must be True"):
        module.validate_research_evidence_bundle_score_payload(payload)


def test_report_payload_and_digest_are_deterministic() -> None:
    module = api()
    source_inputs = (
        bundle_input(redacted_bundle_ref="bundle-watch", traceability_score=d("0.600000")),
        bundle_input(redacted_bundle_ref="bundle-pass"),
        bundle_input(redacted_bundle_ref="bundle-block", traceability_score=d("0.400000")),
    )

    first = module.build_research_evidence_bundle_score_report(source_inputs)
    second = module.build_research_evidence_bundle_score_report(tuple(reversed(source_inputs)))

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert len(first.rows[0].derived_validation_digest) == 64

    payload = module.research_evidence_bundle_score_payload(first)
    assert payload == first.payload
    assert payload["bundle_count"] == "3"
    assert payload["average_evidence_bundle_quality_score"] == "0.805000"
    assert payload["rows"][0]["redacted_bundle_ref"] == "bundle-block"
    assert payload["rows"][0]["evidence_bundle_quality_score"] == "0.735000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_payload_has_no_int_or_float(payload)
    dumps(payload, sort_keys=True)

    object.__setattr__(first, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_evidence_bundle_score_payload(first)

    rebuilt = module.ResearchEvidenceBundleScoreReport(**public_field_values(second))
    assert rebuilt == second
