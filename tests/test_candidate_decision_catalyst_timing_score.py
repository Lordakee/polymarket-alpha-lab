from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
CATALYST_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
RESOLUTION_AT = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_catalyst_timing_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "candidate-decision-catalyst-timing-score-test",
        "near_term_window_seconds": d("259200.000000"),
        "minimum_confidence_score": d("0.500000"),
        "minimum_specificity_score": d("0.500000"),
        "minimum_freshness_score": d("0.400000"),
        "pass_score_floor": d("0.750000"),
        "watch_score_floor": d("0.400000"),
        "confidence_weight": d("0.300000"),
        "specificity_weight": d("0.300000"),
        "freshness_weight": d("0.200000"),
        "timing_weight": d("0.100000"),
        "liquidity_weight": d("0.050000"),
        "edge_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.CandidateDecisionCatalystTimingScoreConfig(**values)


def score_input(**overrides: object) -> Any:
    module = api()
    values = {
        "generated_at": GENERATED_AT,
        "candidate_ref": "candidate_ref_alpha",
        "next_catalyst_at": CATALYST_AT,
        "resolution_at": RESOLUTION_AT,
        "catalyst_confidence_score": d("0.900000"),
        "catalyst_specificity_score": d("0.900000"),
        "evidence_freshness_score": d("0.800000"),
        "liquidity_depth_score": d("0.700000"),
        "edge_quality_score": d("0.600000"),
    }
    values.update(overrides)
    return module.CandidateDecisionCatalystTimingScoreInput(**values)


def score(subject: object | None = None, *, config: object | None = None) -> Any:
    module = api()
    return module.score_candidate_decision_catalyst_timing_score(
        score_input() if subject is None else subject,
        config=cfg() if config is None else config,
    )


def assert_no_float_or_int(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)
        return
    assert type(value) not in (float, int)


def unsafe_terms() -> tuple[str, ...]:
    return (
        "".join(("se", "cret")),
        "".join(("to", "ken")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("tr", "ade")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("reco", "mmendation")),
        "".join(("posi", "tion")),
        "".join(("dsn",)),
        "".join(("tab", "le")),
        "".join(("sl", "ug")),
        "".join(("ques", "tion")),
        "".join(("u", "rl")),
    )


def test_future_catalyst_before_resolution_scores_pass_with_decimal_report() -> None:
    report = score()

    assert report.timing_status == "pass"
    assert report.timing_fit_score == d("0.831667")
    assert report.timing_proximity_score == d("0.666667")
    assert report.seconds_until_catalyst == d("86400.000000")
    assert report.seconds_until_resolution == d("259200.000000")
    assert report.reason_codes == ("catalyst_timing_fit_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    for item in (cfg(), score_input(), report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(("_score", "_seconds", "_weight", "_floor")):
                assert type(value) is Decimal


def test_catalyst_at_or_before_generated_at_blocks_manual_priority() -> None:
    before = score(
        score_input(next_catalyst_at=GENERATED_AT - timedelta(seconds=1)),
    )
    equal = score(score_input(next_catalyst_at=GENERATED_AT))

    for report in (before, equal):
        assert report.timing_status == "block"
        assert report.timing_fit_score == d("0.000000")
        assert report.timing_proximity_score == d("0.000000")
        assert "catalyst_not_after_generated_at" in report.reason_codes
        assert report.reason_codes[0] == "catalyst_timing_fit_block"


def test_catalyst_after_resolution_blocks_manual_priority() -> None:
    report = score(
        score_input(
            next_catalyst_at=RESOLUTION_AT + timedelta(seconds=1),
        ),
    )

    assert report.timing_status == "block"
    assert report.timing_fit_score == d("0.000000")
    assert report.seconds_until_catalyst == d("259201.000000")
    assert report.seconds_until_resolution == d("259200.000000")
    assert report.reason_codes == (
        "catalyst_timing_fit_block",
        "catalyst_after_resolution_at",
    )


def test_missing_confidence_and_specificity_block_even_with_valid_dates() -> None:
    report = score(
        score_input(
            catalyst_confidence_score=d("0.000000"),
            catalyst_specificity_score=d("0.000000"),
        ),
    )

    assert report.timing_status == "block"
    assert report.timing_fit_score == d("0.291667")
    assert report.reason_codes == (
        "catalyst_timing_fit_block",
        "catalyst_confidence_missing",
        "catalyst_specificity_missing",
    )


def test_decimal_type_rejection_and_hard_flags_are_exact() -> None:
    module = api()

    with pytest.raises(ValueError, match="catalyst_confidence_score must be a Decimal"):
        score_input(catalyst_confidence_score=1)
    with pytest.raises(ValueError, match="liquidity_depth_score must be a Decimal"):
        score_input(liquidity_depth_score=0.5)
    with pytest.raises(ValueError, match="edge_quality_score must be a Decimal"):
        score_input(edge_quality_score=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="near_term_window_seconds must be a Decimal"):
        cfg(near_term_window_seconds=259200)
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(score(), readonly=False)

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.CandidateDecisionCatalystTimingScoreConfig):
            pass

    with pytest.raises(FrozenInstanceError):
        score().timing_status = "watch"  # type: ignore[misc]


def test_public_payload_rejects_leaks_and_keeps_status_vocabulary_public() -> None:
    module = api()

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public surface"):
            score_input(candidate_ref=f"candidate_ref_{term}")

    report = score()
    payload = module.candidate_decision_catalyst_timing_score_payload(report)
    rendered = json.dumps(payload, sort_keys=True).lower()

    assert payload["candidate_ref"] == "candidate_ref_alpha"
    assert payload["timing_status"] == "pass"
    assert "ready" not in rendered
    assert "blocked" not in rendered
    assert "matched" not in rendered
    assert "supported" not in rendered
    assert "market_id" not in rendered
    assert "market_slug" not in rendered
    assert "question" not in rendered
    assert "http" not in rendered
    assert_no_float_or_int(payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_slug"] = "alpha"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_catalyst_timing_score_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["candidate_ref"] = "candidate_ref_" + "".join(("to", "ken"))
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_catalyst_timing_score_payload(
            unsafe_value_payload,
        )


def test_digest_payload_and_report_consistency_are_validated() -> None:
    module = api()
    report = score()
    payload = module.candidate_decision_catalyst_timing_score_payload(report)

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["next_catalyst_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["timing_fit_score"] == "0.831667"
    assert payload["report_validation_digest"] == report.report_validation_digest
    assert len(report.report_validation_digest) == 64
    assert module.validate_candidate_decision_catalyst_timing_score_payload(payload)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="timing_fit_score must match"):
        replace(report, timing_fit_score=d("0.100000"))
    with pytest.raises(ValueError, match="report_validation_digest must match"):
        replace(report, report_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["timing_fit_score"] = "0.100000"
    with pytest.raises(ValueError, match="report_validation_digest must match"):
        module.validate_candidate_decision_catalyst_timing_score_payload(
            tampered_payload,
        )


def test_public_api_and_static_surface_are_report_only() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_CATALYST_TIMING_SCORE_CONFIG_VERSION",
        "CandidateDecisionCatalystTimingScoreConfig",
        "CandidateDecisionCatalystTimingScoreInput",
        "CandidateDecisionCatalystTimingScoreReport",
        "score_candidate_decision_catalyst_timing_score",
        "candidate_decision_catalyst_timing_score_payload",
        "validate_candidate_decision_catalyst_timing_score_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    for public_name in public_names:
        lower_name = public_name.lower()
        for term in unsafe_terms():
            assert term not in lower_name

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "subprocess",
        "Path(",
        "open(",
        ".write(",
        ".read(",
    ):
        assert forbidden not in source
