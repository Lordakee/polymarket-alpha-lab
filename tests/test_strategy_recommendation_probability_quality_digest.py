from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import inspect
import json
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.strategy_recommendation_probability_quality_digest import (
    DEFAULT_STRATEGY_RECOMMENDATION_PROBABILITY_QUALITY_DIGEST_CONFIG_VERSION,
    StrategyRecommendationProbabilityQualityDigestCandidate,
    StrategyRecommendationProbabilityQualityDigestConfig,
    StrategyRecommendationProbabilityQualityDigestReport,
    StrategyRecommendationProbabilityQualityDigestRollup,
    build_strategy_recommendation_probability_quality_digest_report,
    strategy_recommendation_probability_quality_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def _candidate(
    candidate_id: str,
    *,
    market_slug: str | None = None,
    condition_id: str | None = None,
    forecast_probability: str = "0.600000",
    market_probability: str = "0.540000",
    forecast_confidence: str = "0.900000",
    ensemble_min_probability: str = "0.580000",
    ensemble_max_probability: str = "0.620000",
    probability_generated_at: datetime | None = None,
    rationale: str = "price/value gap backed by calibrated ensemble",
    rationale_gap_codes: tuple[str, ...] = (),
    recommendation_rank: str = "1",
    reason_codes: tuple[str, ...] = ("source_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id=candidate_id,
        market_slug=market_slug or f"{candidate_id}-market",
        condition_id=condition_id or f"{candidate_id}-condition",
        forecast_probability=Decimal(forecast_probability),
        market_probability=Decimal(market_probability),
        forecast_confidence=Decimal(forecast_confidence),
        ensemble_min_probability=Decimal(ensemble_min_probability),
        ensemble_max_probability=Decimal(ensemble_max_probability),
        probability_generated_at=probability_generated_at or GENERATED_AT - timedelta(minutes=30),
        rationale=rationale,
        rationale_gap_codes=rationale_gap_codes,
        recommendation_rank=Decimal(recommendation_rank),
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_empty_input_returns_report_only_blocked_decimal_rollup() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "provide_recommendation_candidates"
    assert report.reason_codes == ("missing_candidates",)
    assert report.rows == ()
    assert report.rollup == StrategyRecommendationProbabilityQualityDigestRollup(
        candidate_count=Decimal("0"),
        pass_count=Decimal("0"),
        watch_count=Decimal("0"),
        blocked_count=Decimal("0"),
        average_forecast_confidence=Decimal("0.000000"),
        average_probability_gap=Decimal("0.000000"),
        average_ensemble_dispersion=Decimal("0.000000"),
        stale_context_count=Decimal("0"),
        unresolved_rationale_gap_count=Decimal("0"),
        reason_code_counts=(("missing_candidates", Decimal("1")),),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_quality_candidates_pass_with_decimal_rows_and_rollup() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (
            _candidate("beta", recommendation_rank="2"),
            _candidate("alpha", recommendation_rank="1", forecast_confidence="0.950000"),
        ),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )

    assert report.digest_status == "pass"
    assert report.recommended_next_step == "continue_recommendation_review"
    assert report.reason_codes == ("probability_quality_ready",)
    assert tuple(row.candidate_id for row in report.rows) == ("alpha", "beta")
    assert all(row.quality_status == "pass" for row in report.rows)
    assert all(row.reason_codes == ("probability_quality_ready",) for row in report.rows)
    assert all(row.probability_generated_at.tzinfo is UTC for row in report.rows)
    assert report.rollup.candidate_count == Decimal("2")
    assert report.rollup.pass_count == Decimal("2")
    assert report.rollup.average_forecast_confidence == Decimal("0.925000")
    assert report.rollup.average_probability_gap == Decimal("0.060000")
    assert report.rollup.average_ensemble_dispersion == Decimal("0.040000")


def test_watch_dispersion_candidate_rolls_up_stable_reason_codes() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (
            _candidate("ready", recommendation_rank="2"),
            _candidate(
                "wide",
                recommendation_rank="1",
                ensemble_min_probability="0.450000",
                ensemble_max_probability="0.700000",
                reason_codes=("source_ready", "wide_source_range"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(
            max_watch_ensemble_dispersion=Decimal("0.100000"),
            max_blocking_ensemble_dispersion=Decimal("0.300000"),
        ),
    )

    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_probability_quality_watchlist"
    assert report.reason_codes == ("ensemble_dispersion_watch",)
    assert report.rows[0].candidate_id == "wide"
    assert report.rows[0].quality_status == "watch"
    assert report.rows[0].ensemble_dispersion == Decimal("0.250000")
    assert report.rows[0].reason_codes == ("ensemble_dispersion_watch", "wide_source_range")
    assert report.rollup.reason_code_counts == (
        ("ensemble_dispersion_watch", Decimal("1")),
        ("probability_quality_ready", Decimal("1")),
        ("wide_source_range", Decimal("1")),
    )


def test_blocked_stale_context_dominates_digest_status() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (
            _candidate("fresh", recommendation_rank="1"),
            _candidate(
                "old",
                recommendation_rank="2",
                probability_generated_at=GENERATED_AT - timedelta(hours=7),
            ),
        ),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(
            max_probability_context_age_seconds=Decimal("3600"),
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "refresh_probability_context"
    assert report.reason_codes == ("stale_probability_context",)
    assert report.rollup.stale_context_count == Decimal("1")
    assert report.rows[1].candidate_id == "old"
    assert report.rows[1].quality_status == "blocked"
    assert report.rows[1].probability_context_age_seconds == Decimal("25200")


def test_missing_rationale_is_blocked_and_gap_codes_are_aggregated() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (
            _candidate("blank", rationale=""),
            _candidate(
                "gapped",
                rationale_gap_codes=("missing_counterargument", "missing_resolution_source"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )

    assert report.digest_status == "blocked"
    assert report.reason_codes == (
        "missing_counterargument",
        "missing_rationale",
        "missing_resolution_source",
        "unresolved_rationale_gap",
    )
    assert report.rollup.unresolved_rationale_gap_count == Decimal("2")
    assert report.rollup.reason_code_counts == (
        ("missing_counterargument", Decimal("1")),
        ("missing_rationale", Decimal("1")),
        ("missing_resolution_source", Decimal("1")),
        ("unresolved_rationale_gap", Decimal("1")),
    )


def test_row_sorting_uses_rank_then_market_condition_candidate() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (
            _candidate("zeta", market_slug="b-market", condition_id="z-condition"),
            _candidate("alpha", market_slug="a-market", condition_id="b-condition"),
            _candidate("beta", market_slug="a-market", condition_id="a-condition"),
            _candidate("ranked", recommendation_rank="0"),
        ),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )

    assert tuple(row.candidate_id for row in report.rows) == (
        "ranked",
        "beta",
        "alpha",
        "zeta",
    )


def test_payload_helper_emits_decimal_strings_and_no_floats() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (_candidate("alpha"),),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )

    payload = strategy_recommendation_probability_quality_digest_payload(report)
    rendered = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["rollup"]["candidate_count"] == "1.000000"
    assert payload["rows"][0]["forecast_probability"] == "0.600000"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert "0.600000" in rendered
    assert strategy_recommendation_probability_quality_digest_payload(payload) == payload


def test_report_rejects_tampered_derived_rollup() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (_candidate("alpha"),),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )
    tampered_rollup = StrategyRecommendationProbabilityQualityDigestRollup(
        candidate_count=Decimal("2"),
        pass_count=Decimal("1"),
        watch_count=Decimal("0"),
        blocked_count=Decimal("0"),
        average_forecast_confidence=report.rollup.average_forecast_confidence,
        average_probability_gap=report.rollup.average_probability_gap,
        average_ensemble_dispersion=report.rollup.average_ensemble_dispersion,
        stale_context_count=report.rollup.stale_context_count,
        unresolved_rationale_gap_count=report.rollup.unresolved_rationale_gap_count,
        reason_code_counts=report.rollup.reason_code_counts,
    )

    with pytest.raises(ValueError, match="rollup"):
        StrategyRecommendationProbabilityQualityDigestReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            digest_status=report.digest_status,
            recommended_next_step=report.recommended_next_step,
            rows=report.rows,
            rollup=tampered_rollup,
            reason_codes=report.reason_codes,
        )


def test_report_uses_tamper_evident_derived_validation_digest() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (_candidate("alpha"),),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    object.__setattr__(report.rows[0], "forecast_confidence", Decimal("0.010000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_recommendation_probability_quality_digest_payload(report)


def test_public_payload_dict_path_rejects_tampering_numerics_and_unsafe_surfaces() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (_candidate("alpha"),),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )
    payload = strategy_recommendation_probability_quality_digest_payload(report)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_recommendation_probability_quality_digest_payload(missing_digest)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_recommendation_probability_quality_digest_payload(
            {**payload, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="Decimal"):
        strategy_recommendation_probability_quality_digest_payload(
            {**payload, "rollup": {**payload["rollup"], "candidate_count": 1}},
        )
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_probability_quality_digest_payload(
            {**payload, "network_url": "disabled"},
        )
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_probability_quality_digest_payload(
            {**payload, "rows": [{**payload["rows"][0], "rationale": "persist wallet key"}]},
        )


def test_payload_helper_rejects_tampered_public_payload_surface() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (_candidate("alpha"),),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )

    object.__setattr__(report, "ord" "er_id", "latent public field")

    with pytest.raises(ValueError, match="unsafe surface field"):
        strategy_recommendation_probability_quality_digest_payload(report)


def test_payload_helper_revalidates_report_only_flags() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (_candidate("alpha"),),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )

    object.__setattr__(report, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        strategy_recommendation_probability_quality_digest_payload(report)


def test_validation_rejects_float_naive_datetime_bad_flags_and_inverted_thresholds() -> None:
    config = StrategyRecommendationProbabilityQualityDigestConfig()

    unsafe = _candidate("float", forecast_probability="0.600000")
    unsafe.forecast_probability = 0.6
    with pytest.raises(ValueError, match="float"):
        build_strategy_recommendation_probability_quality_digest_report(
            (unsafe,),
            generated_at=GENERATED_AT,
            config=config,
        )

    naive = _candidate("naive")
    naive.probability_generated_at = datetime(2026, 7, 2, 12, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        build_strategy_recommendation_probability_quality_digest_report(
            (naive,),
            generated_at=GENERATED_AT,
            config=config,
        )

    with pytest.raises(ValueError, match="paper_only"):
        build_strategy_recommendation_probability_quality_digest_report(
            (_candidate("unsafe", paper_only=False),),
            generated_at=GENERATED_AT,
            config=config,
        )

    with pytest.raises(ValueError, match="max_watch_ensemble_dispersion"):
        StrategyRecommendationProbabilityQualityDigestConfig(
            max_watch_ensemble_dispersion=Decimal("0.400000"),
            max_blocking_ensemble_dispersion=Decimal("0.300000"),
        )


@pytest.mark.parametrize(
    ("candidate", "match"),
    (
        (_candidate("sk_live_secret"), "candidate_id contains sensitive material"),
        (
            _candidate("safe-id", rationale="wallet private key leaked here"),
            "rationale contains sensitive material",
        ),
        (
            _candidate("safe-id", rationale_gap_codes=("bearer_token_missing",)),
            "rationale_gap_codes contains sensitive material",
        ),
        (
            _candidate("safe-id", reason_codes=("source_ready", "api_key_observed")),
            "reason_codes contains sensitive material",
        ),
    ),
)
def test_sensitive_candidate_text_is_rejected_before_payload(
    candidate: SimpleNamespace,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        build_strategy_recommendation_probability_quality_digest_report(
            (candidate,),
            generated_at=GENERATED_AT,
            config=StrategyRecommendationProbabilityQualityDigestConfig(),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "auth_token",
        "wallet",
        "order_id",
        "cancel_url",
        "replace_request",
        "live_trading_enabled",
        "network_url",
        "database_dsn",
        "persist_path",
    ),
)
def test_unused_live_surface_candidate_fields_are_rejected(field_name: str) -> None:
    candidate = _candidate("safe-id")
    setattr(candidate, field_name, "secret-live-value")

    with pytest.raises(ValueError, match="unsafe surface field"):
        build_strategy_recommendation_probability_quality_digest_report(
            (candidate,),
            generated_at=GENERATED_AT,
            config=StrategyRecommendationProbabilityQualityDigestConfig(),
        )


def test_timezone_normalization_uses_utc() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_strategy_recommendation_probability_quality_digest_report(
        (
            _candidate(
                "offset",
                probability_generated_at=datetime(2026, 7, 2, 7, 30, tzinfo=eastern),
            ),
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=eastern),
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].probability_generated_at == GENERATED_AT - timedelta(minutes=30)


def test_public_dataclasses_are_frozen_and_exact() -> None:
    config = StrategyRecommendationProbabilityQualityDigestConfig()
    report = build_strategy_recommendation_probability_quality_digest_report(
        (_candidate("alpha"),),
        generated_at=GENERATED_AT,
        config=config,
    )

    with pytest.raises(FrozenInstanceError):
        report.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].candidate_id = "mutated"  # type: ignore[misc]
    with pytest.raises(TypeError):
        class BadConfig(StrategyRecommendationProbabilityQualityDigestConfig):
            pass

    with pytest.raises(ValueError, match="report"):
        StrategyRecommendationProbabilityQualityDigestReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            digest_status="pass",
            recommended_next_step=report.recommended_next_step,
            rows=report.rows,
            rollup=report.rollup,
            reason_codes=("probability_quality_ready",),
            paper_only=False,
        )
    assert asdict(config)["config_version"] == (
        DEFAULT_STRATEGY_RECOMMENDATION_PROBABILITY_QUALITY_DIGEST_CONFIG_VERSION
    )
    assert type(report.rows[0]) is StrategyRecommendationProbabilityQualityDigestCandidate


def test_public_numeric_count_ratio_fields_are_decimal_only() -> None:
    report = build_strategy_recommendation_probability_quality_digest_report(
        (_candidate("alpha"),),
        generated_at=GENERATED_AT,
        config=StrategyRecommendationProbabilityQualityDigestConfig(),
    )
    public_objects = (report.rollup, *report.rows)

    for public_object in public_objects:
        for name, value in asdict(public_object).items():
            if _field_name_is_numeric(name):
                assert type(value) is Decimal, name


def test_static_forbidden_surface_terms_are_absent() -> None:
    import polymarket_alpha_lab.strategy_recommendation_probability_quality_digest as module

    public_text = " ".join(
        name
        for name, value in inspect.getmembers(module)
        if not name.startswith("_") and getattr(value, "__module__", module.__name__) == module.__name__
    ).lower()
    source = inspect.getsource(module).lower()

    forbidden_name_fragments = (
        "auth",
        "broker",
        "db",
        "file",
        "live",
        "network",
        "order",
        "sign",
        "trade",
        "wallet",
    )
    for fragment in forbidden_name_fragments:
        assert fragment not in public_text

    forbidden_source_terms = (
        "requests",
        "httpx",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "socket",
        "subprocess",
        "open(",
        "order",
        "wallet",
        "broker",
        "signing",
        "advice",
    )
    for term in forbidden_source_terms:
        assert term not in source


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(child for item in value.values() for child in _walk_values(item))
    if isinstance(value, (list, tuple)):
        return tuple(child for item in value for child in _walk_values(item))
    return (value,)


def _field_name_is_numeric(name: str) -> bool:
    numeric_fragments = (
        "age",
        "confidence",
        "count",
        "dispersion",
        "gap",
        "probability",
        "rank",
        "ratio",
        "seconds",
        "share",
    )
    return (
        name != "reason_code_counts"
        and name != "rationale"
        and name != "rationale_gap_codes"
        and not name.endswith("_generated_at")
        and any(fragment in name for fragment in numeric_fragments)
    )
