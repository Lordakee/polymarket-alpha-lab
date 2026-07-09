from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_team_review_confidence_decay_report import (
    DEFAULT_RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_STATUSES,
    ResearchStrategyTeamReviewConfidenceDecayConfig,
    ResearchStrategyTeamReviewConfidenceDecayInput,
    ResearchStrategyTeamReviewConfidenceDecayReport,
    ResearchStrategyTeamReviewConfidenceDecayRow,
    build_research_strategy_team_review_confidence_decay_report,
    research_strategy_team_review_confidence_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyTeamReviewConfidenceDecayConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
        ),
        "fresh_confidence_age_seconds": d("1800.000000"),
        "stale_confidence_age_seconds": d("7200.000000"),
        "watch_confidence_drop": d("0.100000"),
        "block_confidence_drop": d("0.250000"),
        "min_pass_current_confidence_score": d("0.700000"),
        "min_watch_current_confidence_score": d("0.500000"),
        "min_pass_decay_adjusted_confidence_score": d("0.650000"),
        "min_watch_decay_adjusted_confidence_score": d("0.450000"),
        "max_pass_decay_pressure_score": d("0.200000"),
        "max_watch_decay_pressure_score": d("0.450000"),
        "min_pass_review_evidence_freshness_score": d("0.700000"),
        "min_watch_review_evidence_freshness_score": d("0.500000"),
        "min_pass_team_calibration_score": d("0.700000"),
        "min_watch_team_calibration_score": d("0.500000"),
        "min_pass_reviewer_agreement_score": d("0.800000"),
        "min_watch_reviewer_agreement_score": d("0.600000"),
        "max_pass_review_latency_pressure": d("0.200000"),
        "max_watch_review_latency_pressure": d("0.400000"),
    }
    values.update(overrides)
    return ResearchStrategyTeamReviewConfidenceDecayConfig(**values)


def review_input(**overrides: object) -> ResearchStrategyTeamReviewConfidenceDecayInput:
    values = {
        "team_ref": "team-alpha",
        "review_ref": "review-alpha",
        "reviewed_at": GENERATED_AT - timedelta(seconds=900),
        "last_confidence_update_at": GENERATED_AT - timedelta(seconds=600),
        "baseline_confidence_score": d("0.900000"),
        "current_confidence_score": d("0.880000"),
        "review_evidence_freshness_score": d("0.900000"),
        "team_calibration_score": d("0.900000"),
        "reviewer_agreement_score": d("0.900000"),
        "review_latency_pressure": d("0.050000"),
    }
    values.update(overrides)
    return ResearchStrategyTeamReviewConfidenceDecayInput(**values)


def report(
    *rows: ResearchStrategyTeamReviewConfidenceDecayInput,
    cfg: ResearchStrategyTeamReviewConfidenceDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyTeamReviewConfidenceDecayReport:
    return build_research_strategy_team_review_confidence_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_scores_review_confidence_decay_and_rolls_up_status() -> None:
    summary = report(
        review_input(),
        review_input(
            team_ref="team-alpha",
            review_ref="review-beta",
            reviewed_at=GENERATED_AT - timedelta(seconds=5000),
            last_confidence_update_at=GENERATED_AT - timedelta(seconds=4500),
            baseline_confidence_score=d("0.850000"),
            current_confidence_score=d("0.720000"),
            review_evidence_freshness_score=d("0.600000"),
            team_calibration_score=d("0.600000"),
            reviewer_agreement_score=d("0.700000"),
            review_latency_pressure=d("0.300000"),
        ),
        review_input(
            team_ref="team-beta",
            review_ref="review-gamma",
            reviewed_at=GENERATED_AT - timedelta(seconds=7800),
            last_confidence_update_at=GENERATED_AT - timedelta(seconds=7200),
            baseline_confidence_score=d("0.850000"),
            current_confidence_score=d("0.420000"),
            review_evidence_freshness_score=d("0.350000"),
            team_calibration_score=d("0.400000"),
            reviewer_agreement_score=d("0.500000"),
            review_latency_pressure=d("0.700000"),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
    )
    assert summary.review_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_confidence_drop == d("0.193333")
    assert summary.mean_decay_pressure_score == d("0.348889")
    assert summary.mean_decay_adjusted_confidence_score == d("0.483511")
    assert summary.lowest_decay_adjusted_confidence_score == d("0.148400")
    assert summary.highest_confidence_drop == d("0.430000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "review_confidence_decay_block",
        "confidence_drop_review",
        "current_confidence_review",
        "evidence_freshness_review",
        "team_calibration_review",
        "reviewer_agreement_review",
        "review_latency_review",
        "decay_pressure_review",
        "adjusted_confidence_review",
        "confidence_age_review",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyTeamReviewConfidenceDecayRow)
    assert blocked.aggregate_row_number == d("1.000000")
    assert blocked.team_ref == "team-beta"
    assert len(blocked.review_hash) == 64
    assert blocked.confidence_age_seconds == d("7200.000000")
    assert blocked.confidence_age_pressure == d("1.000000")
    assert blocked.confidence_drop == d("0.430000")
    assert blocked.decay_pressure_score == d("0.646667")
    assert blocked.decay_adjusted_confidence_score == d("0.148400")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "adjusted_confidence_block",
        "confidence_age_block",
        "confidence_drop_block",
        "current_confidence_block",
        "decay_pressure_block",
        "evidence_freshness_block",
        "review_latency_block",
        "reviewer_agreement_block",
        "team_calibration_block",
    )

    watched = summary.rows[1]
    assert watched.aggregate_row_number == d("2.000000")
    assert watched.confidence_age_pressure == d("0.500000")
    assert watched.confidence_drop == d("0.130000")
    assert watched.decay_pressure_score == d("0.338333")
    assert watched.decay_adjusted_confidence_score == d("0.476400")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "adjusted_confidence_watch",
        "confidence_age_watch",
        "confidence_drop_watch",
        "decay_pressure_watch",
        "evidence_freshness_watch",
        "review_latency_watch",
        "reviewer_agreement_watch",
        "team_calibration_watch",
    )

    passed = summary.rows[2]
    assert passed.aggregate_row_number == d("3.000000")
    assert passed.confidence_age_pressure == d("0.000000")
    assert passed.confidence_drop == d("0.020000")
    assert passed.decay_pressure_score == d("0.061667")
    assert passed.decay_adjusted_confidence_score == d("0.825733")
    assert passed.status == "pass"
    assert passed.reason_codes == ("review_confidence_decay_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True
    assert len(passed.derived_validation_digest) == 64


def test_empty_report_blocks_without_rows_or_unsafe_surface() -> None:
    summary = report()

    assert summary.status == "block"
    assert summary.review_count == d("0.000000")
    assert summary.pass_count == d("0.000000")
    assert summary.watch_count == d("0.000000")
    assert summary.block_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == (
        "review_confidence_decay_block",
        "review_confidence_decay_no_inputs",
    )
    assert summary.reason_code_counts == (
        ("review_confidence_decay_no_inputs", d("1.000000")),
    )
    assert_decimal_only_numerics(summary)


def test_public_payload_is_deterministic_hashed_decimal_and_digest_guarded() -> None:
    sensitive_ref = (
        "candidate-alpha market-alpha will resolve "
        "https://private.example/path?api_key=hidden-token table=db.events"
    )
    first_payload = research_strategy_team_review_confidence_decay_report_payload(
        report(review_input(review_ref=sensitive_ref)),
    )
    second_payload = research_strategy_team_review_confidence_decay_report_payload(
        report(review_input(review_ref=sensitive_ref)),
    )
    encoded = json.dumps(first_payload, sort_keys=True).lower()

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["review_count"] == "1.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["review_hash"]) == 64
    assert first_payload["rows"][0]["decay_adjusted_confidence_score"] == "0.825733"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert first_payload["derived_validation_digest"] == payload_digest(first_payload)
    assert_no_decimal_or_raw_numeric_values(first_payload)

    forbidden_payload_fragments = (
        "candidate-alpha",
        "market-alpha",
        "will resolve",
        "https://",
        "private.example",
        "api_key",
        "hidden-token",
        "table=",
        "db.events",
        "review_ref",
    )
    assert all(fragment not in encoded for fragment in forbidden_payload_fragments)

    tampered_payload = json.loads(json.dumps(first_payload))
    tampered_payload["rows"][0]["decay_adjusted_confidence_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_team_review_confidence_decay_report_payload(tampered_payload)

    numeric_payload = json.loads(json.dumps(first_payload))
    numeric_payload["review_count"] = 1
    with pytest.raises(ValueError, match="review_count"):
        research_strategy_team_review_confidence_decay_report_payload(numeric_payload)

    unsafe_payload = json.loads(json.dumps(first_payload))
    unsafe_payload["candidate_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_team_review_confidence_decay_report_payload(unsafe_payload)

    unsafe_nested_payload = json.loads(json.dumps(first_payload))
    unsafe_nested_payload["rows"][0]["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_team_review_confidence_decay_report_payload(
            unsafe_nested_payload,
        )


def test_validation_rejects_non_decimal_times_duplicates_flags_and_tampering() -> None:
    with pytest.raises(ValueError, match="baseline_confidence_score"):
        review_input(baseline_confidence_score=0.9)
    with pytest.raises(ValueError, match="review_latency_pressure"):
        review_input(review_latency_pressure=d("-0.1"))
    with pytest.raises(ValueError, match="reviewed_at"):
        review_input(reviewed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="generated_at"):
        report(review_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="last_confidence_update_at"):
        report(
            review_input(
                last_confidence_update_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="last_confidence_update_at"):
        review_input(
            reviewed_at=GENERATED_AT - timedelta(seconds=60),
            last_confidence_update_at=GENERATED_AT - timedelta(seconds=120),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(review_input(review_ref="same"), review_input(review_ref="same"))
    with pytest.raises(ValueError, match="threshold"):
        config(min_pass_current_confidence_score=d("0.400000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="watch_confidence_drop"):
        config(watch_confidence_drop=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            review_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )

    summary = report(review_input())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary.rows[0],
            decay_adjusted_confidence_score=d("0.500000"),
            derived_validation_digest=summary.rows[0].derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            review_count=d("0.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )


def test_public_dataclasses_are_frozen_and_module_has_no_forbidden_surfaces() -> None:
    summary = report(review_input())
    row = summary.rows[0]

    assert is_dataclass(ResearchStrategyTeamReviewConfidenceDecayConfig)
    assert is_dataclass(ResearchStrategyTeamReviewConfidenceDecayInput)
    assert is_dataclass(ResearchStrategyTeamReviewConfidenceDecayRow)
    assert is_dataclass(ResearchStrategyTeamReviewConfidenceDecayReport)
    assert RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)

    source = Path(
        "src/polymarket_alpha_lab/research_strategy_team_review_confidence_decay_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "broker",
        "private_key",
        "investment_advice",
        "live_trading",
        "sizing",
        "recommendation",
        "requests.",
        "urllib",
        "sqlite",
        "sqlalchemy",
        "open(",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "api_key",
    ):
        assert forbidden not in lowered
    assert not re.search(r"\b(auth|wallet|broker|order|trade|sizing)\b", lowered)

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "open"


def assert_decimal_only_numerics(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_decimal_only_numerics(item)


def assert_no_decimal_or_raw_numeric_values(value: Any) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"payload numeric value must be string encoded: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_decimal_or_raw_numeric_values(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_no_decimal_or_raw_numeric_values(item)


def payload_digest(payload: dict[str, Any]) -> str:
    comparable = json.loads(json.dumps(payload))
    comparable.pop("derived_validation_digest", None)
    canonical = json.dumps(
        comparable,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
