from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal

import pytest


CONFIG_VERSION = "market-candidate-due-diligence-depth-report-v0"


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_candidate_due_diligence_depth_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object):
    depth = module()
    values = {
        "official_source_count": d("2.000000"),
        "independent_source_count": d("3.000000"),
        "domain_specialist_review_count": d("2.000000"),
        "resolution_rule_clarity_ready": True,
        "source_conflict_resolved": True,
        "cost_model_checked": True,
        "team_memory_checked": True,
        "manual_review_notes_redacted": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return depth.build_market_candidate_due_diligence_depth_report(**values)


def test_deep_diligence_report_scores_ready_candidate_and_public_payload() -> None:
    depth = module()
    report = build_report()

    assert is_dataclass(report)
    assert report.config_version == CONFIG_VERSION
    assert report.diligence_depth_score == d("1.000000")
    assert report.depth_band == "deep"
    assert report.missing_review_count == d("0.000000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ("diligence_depth_ready",)
    assert report.ready_ratio == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = depth.market_candidate_due_diligence_depth_report_payload(report)
    assert payload["official_source_count"] == "2.000000"
    assert payload["diligence_depth_score"] == "1.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)
    _assert_public_payload_has_no_blocked_terms(payload)


def test_missing_reviews_create_watch_band_and_attention_codes() -> None:
    report = build_report(
        official_source_count=d("1.000000"),
        independent_source_count=d("1.000000"),
        domain_specialist_review_count=d("0.000000"),
        cost_model_checked=False,
        team_memory_checked=False,
    )

    assert report.depth_band == "watch"
    assert report.diligence_depth_score == d("0.500000")
    assert report.ready_ratio == d("0.500000")
    assert report.missing_review_count == d("4.000000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "official_source_depth_below_target",
        "independent_source_depth_below_target",
        "domain_specialist_review_missing",
        "cost_model_unchecked",
        "team_memory_unchecked",
    )


def test_unresolved_required_flags_block_even_with_sufficient_sources() -> None:
    report = build_report(
        resolution_rule_clarity_ready=False,
        source_conflict_resolved=False,
        manual_review_notes_redacted=False,
    )

    assert report.depth_band == "blocked"
    assert report.diligence_depth_score == d("0.700000")
    assert report.ready_ratio == d("0.700000")
    assert report.missing_review_count == d("3.000000")
    assert report.blocked_reason_codes == (
        "resolution_rule_clarity_not_ready",
        "source_conflict_unresolved",
        "manual_review_notes_not_redacted",
    )
    assert report.attention_reason_codes == ()


def test_decimal_only_inputs_and_public_payload_are_enforced() -> None:
    depth = module()

    with pytest.raises(ValueError, match="official_source_count"):
        build_report(official_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independent_source_count"):
        build_report(independent_source_count=2.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_specialist_review_count"):
        build_report(domain_specialist_review_count=d("2.0"))
    with pytest.raises(ValueError, match="official_source_count"):
        build_report(official_source_count=_DecimalSubclass("2.000000"))

    payload = depth.market_candidate_due_diligence_depth_report_payload(build_report())
    with pytest.raises(ValueError, match="Decimal-derived string"):
        depth.market_candidate_due_diligence_depth_report_payload(
            {**payload, "ready_ratio": d("1.000000")},
        )
    with pytest.raises(ValueError, match="public payload numerics"):
        depth.market_candidate_due_diligence_depth_report_payload(
            {**payload, "missing_review_count": 0},
        )


def test_hard_flags_frozen_dataclass_and_digest_tamper_checks() -> None:
    depth = module()
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.depth_band = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        build_report(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = depth.market_candidate_due_diligence_depth_report_payload(report)
    with pytest.raises(ValueError, match="report_only"):
        depth.market_candidate_due_diligence_depth_report_payload(
            {**payload, "report_only": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        depth.market_candidate_due_diligence_depth_report_payload(
            {**payload, "ready_ratio": "0.900000"},
        )


def test_public_surface_rejects_sensitive_and_live_action_language() -> None:
    depth = module()
    payload = depth.market_candidate_due_diligence_depth_report_payload(build_report())

    with pytest.raises(ValueError, match="unsafe public field"):
        depth.market_candidate_due_diligence_depth_report_payload(
            {**payload, "market_id": "hidden"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        depth.market_candidate_due_diligence_depth_report_payload(
            {**payload, "attention_reason_codes": ["wallet_review"]},
        )
    with pytest.raises(ValueError, match="unknown public field"):
        depth.market_candidate_due_diligence_depth_report_payload(
            {**payload, "extra_review_marker": "none"},
        )


def test_output_is_deterministic_and_payload_roundtrips() -> None:
    depth = module()
    first = build_report(
        official_source_count=d("2.000000"),
        independent_source_count=d("3.000000"),
    )
    second = build_report(
        independent_source_count=d("3.000000"),
        official_source_count=d("2.000000"),
    )

    first_payload = depth.market_candidate_due_diligence_depth_report_payload(first)
    second_payload = depth.market_candidate_due_diligence_depth_report_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert depth.market_candidate_due_diligence_depth_report_payload(first_payload) == first_payload


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def _assert_public_payload_has_no_blocked_terms(payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    for blocked in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "database",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "bu" + "y",
        "se" + "ll",
        "rec" + "ommend",
    ):
        assert blocked not in encoded
