from __future__ import annotations

import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

import polymarket_alpha_lab.strategy_recommendation_resolution_confidence_blend_v2 as api


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=timezone(timedelta(hours=2)))
OBSERVED_AT = datetime(2026, 7, 6, 9, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> api.StrategyRecommendationResolutionConfidenceBlendV2Config:
    values: dict[str, object] = {
        "config_version": "resolution-confidence-blend-test-v0",
        "resolution_weight": d("0.600000"),
        "confidence_weight": d("0.400000"),
        "official_source_boost_weight": d("0.100000"),
        "ambiguity_penalty_weight": d("0.200000"),
        "ready_threshold": d("0.700000"),
        "watch_threshold": d("0.500000"),
    }
    values.update(overrides)
    return api.StrategyRecommendationResolutionConfidenceBlendV2Config(**values)


def recommendation(
    candidate_id: str = "candidate-alpha",
    *,
    market_slug: str = "resolution-alpha",
    resolution_evidence_score: Decimal = d("0.800000"),
    confidence_score: Decimal = d("0.700000"),
    official_source_ratio: Decimal = d("0.500000"),
    ambiguity_score: Decimal = d("0.250000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("resolution_packet",),
    **overrides: object,
) -> api.StrategyRecommendationResolutionConfidenceBlendV2Input:
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "market_slug": market_slug,
        "resolution_evidence_score": resolution_evidence_score,
        "confidence_score": confidence_score,
        "official_source_ratio": official_source_ratio,
        "ambiguity_score": ambiguity_score,
        "observed_at": observed_at,
        "reason_codes": reason_codes,
    }
    values.update(overrides)
    return api.StrategyRecommendationResolutionConfidenceBlendV2Input(**values)


def build_report(
    *items: api.StrategyRecommendationResolutionConfidenceBlendV2Input,
) -> api.StrategyRecommendationResolutionConfidenceBlendV2Report:
    return api.build_strategy_recommendation_resolution_confidence_blend_v2(
        items,
        config=cfg(),
        generated_at=GENERATED_AT,
    )


def assert_no_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int(item)


def unsafe_terms() -> tuple[str, ...]:
    return (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )


def test_resolution_confidence_blending_and_report_rollups() -> None:
    report = build_report(
        recommendation("candidate-alpha"),
        recommendation(
            "candidate-beta",
            market_slug="resolution-beta",
            resolution_evidence_score=d("0.600000"),
            confidence_score=d("0.600000"),
            official_source_ratio=d("0.000000"),
            ambiguity_score=d("0.500000"),
        ),
        recommendation(
            "candidate-gamma",
            market_slug="resolution-gamma",
            resolution_evidence_score=d("0.300000"),
            confidence_score=d("0.400000"),
            official_source_ratio=d("0.000000"),
            ambiguity_score=d("0.750000"),
        ),
    )

    rows = {row.candidate_id: row for row in report.rows}
    assert rows["candidate-alpha"].blended_resolution_confidence_score == d("0.760000")
    assert rows["candidate-alpha"].official_source_boost == d("0.050000")
    assert rows["candidate-alpha"].ambiguity_penalty == d("0.050000")
    assert rows["candidate-alpha"].paper_report_status == "ready"
    assert rows["candidate-beta"].blended_resolution_confidence_score == d("0.500000")
    assert rows["candidate-beta"].paper_report_status == "watch"
    assert rows["candidate-gamma"].blended_resolution_confidence_score == d("0.190000")
    assert rows["candidate-gamma"].paper_report_status == "blocked"

    assert report.generated_at == datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
    assert report.row_count == d("3.000000")
    assert report.ready_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.average_blended_resolution_confidence_score == d("0.483333")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_official_source_boosts_and_ambiguity_penalties_move_scores() -> None:
    boosted = build_report(
        recommendation(
            "candidate-boosted",
            official_source_ratio=d("1.000000"),
            ambiguity_score=d("0.000000"),
        ),
        recommendation(
            "candidate-unboosted",
            market_slug="resolution-unboosted",
            official_source_ratio=d("0.000000"),
            ambiguity_score=d("0.000000"),
        ),
        recommendation(
            "candidate-ambiguous",
            market_slug="resolution-ambiguous",
            official_source_ratio=d("1.000000"),
            ambiguity_score=d("1.000000"),
        ),
    )

    rows = {row.candidate_id: row for row in boosted.rows}
    assert rows["candidate-boosted"].official_source_boost == d("0.100000")
    assert rows["candidate-unboosted"].official_source_boost == d("0.000000")
    assert (
        rows["candidate-boosted"].blended_resolution_confidence_score
        - rows["candidate-unboosted"].blended_resolution_confidence_score
    ) == d("0.100000")
    assert rows["candidate-ambiguous"].ambiguity_penalty == d("0.200000")
    assert (
        rows["candidate-boosted"].blended_resolution_confidence_score
        - rows["candidate-ambiguous"].blended_resolution_confidence_score
    ) == d("0.200000")
    assert "official_source_boost_applied" in rows["candidate-boosted"].reason_codes
    assert "ambiguity_penalty_applied" in rows["candidate-ambiguous"].reason_codes


def test_payload_serialization_is_decimal_string_json_ready_and_validated() -> None:
    report = build_report(recommendation())
    payload = api.strategy_recommendation_resolution_confidence_blend_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T10:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["average_blended_resolution_confidence_score"] == "0.760000"
    assert payload["rows"][0]["blended_resolution_confidence_score"] == "0.760000"
    assert payload["rows"][0]["official_source_boost"] == "0.050000"
    assert payload["rows"][0]["ambiguity_penalty"] == "0.050000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert api.validate_strategy_recommendation_resolution_confidence_blend_v2_payload(payload)
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_and_public_numerics_are_decimal_only() -> None:
    assert api.__all__ == (
        "DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_CONFIDENCE_BLEND_V2_CONFIG_VERSION",
        "StrategyRecommendationResolutionConfidenceBlendV2Config",
        "StrategyRecommendationResolutionConfidenceBlendV2Input",
        "StrategyRecommendationResolutionConfidenceBlendV2Row",
        "StrategyRecommendationResolutionConfidenceBlendV2Report",
        "build_strategy_recommendation_resolution_confidence_blend_v2",
        "strategy_recommendation_resolution_confidence_blend_v2_payload",
        "validate_strategy_recommendation_resolution_confidence_blend_v2_payload",
    )
    for exported_name in api.__all__:
        exported = getattr(api, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    report = build_report(recommendation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].paper_report_status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(api.StrategyRecommendationResolutionConfidenceBlendV2Config):
            pass

    with pytest.raises(ValueError, match="resolution_evidence_score must be a Decimal"):
        recommendation(resolution_evidence_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2.000000"))

    for item in (cfg(), recommendation(), report, *report.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(
                (
                    "_score",
                    "_ratio",
                    "_weight",
                    "_threshold",
                    "_boost",
                    "_penalty",
                    "_count",
                ),
            ):
                assert type(value) is Decimal


def test_hard_flags_are_enforced_for_dataclasses_and_payloads() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)

    report = build_report(recommendation())
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)

    payload = api.strategy_recommendation_resolution_confidence_blend_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["report_only"] = False
    with pytest.raises(ValueError, match="report_only must be True"):
        api.validate_strategy_recommendation_resolution_confidence_blend_v2_payload(
            tampered_payload,
        )


def test_digest_tampering_is_rejected_for_reports_and_payloads() -> None:
    report = build_report(recommendation())

    with pytest.raises(ValueError, match="average_blended_resolution_confidence_score"):
        replace(report, average_blended_resolution_confidence_score=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = api.strategy_recommendation_resolution_confidence_blend_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_strategy_recommendation_resolution_confidence_blend_v2_payload(
            tampered_payload,
        )

    object.__setattr__(
        report.rows[0],
        "blended_resolution_confidence_score",
        d("0.100000"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.strategy_recommendation_resolution_confidence_blend_v2_payload(report)


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public surface"):
            recommendation(candidate_id=f"candidate-{term}")

    payload = api.strategy_recommendation_resolution_confidence_blend_v2_payload(
        build_report(recommendation()),
    )
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        api.validate_strategy_recommendation_resolution_confidence_blend_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_value_payload["rows"][0]["candidate_id"] = "candidate-" + "".join(("tr", "ade"))
    with pytest.raises(ValueError, match="unsafe public surface"):
        api.validate_strategy_recommendation_resolution_confidence_blend_v2_payload(
            unsafe_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["row_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        api.validate_strategy_recommendation_resolution_confidence_blend_v2_payload(
            numeric_payload,
        )


def test_module_omits_unsafe_public_surfaces() -> None:
    public_names = set(api.__all__) | {name for name in dir(api) if not name.startswith("_")}
    for public_name in public_names:
        lowered = public_name.lower()
        assert "db" not in lowered
        for term in unsafe_terms():
            assert term not in lowered

    source = inspect.getsource(api)
    forbidden_source_fragments = (
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
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for forbidden in forbidden_source_fragments:
        assert forbidden not in source
