from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "strategy-team-consensus-digest-test-v0"
REVIEWED_AT = datetime(2026, 7, 2, 11, 30, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_team_consensus_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def opinion(
    specialist_id: str,
    *,
    candidate_id: str = "candidate-alpha",
    recommendation_status: str = "support",
    forecast_probability: Decimal = d("0.600000"),
    confidence: Decimal = d("0.800000"),
    source_family: str = "model",
    source_family_status: str = "aligned",
    contradiction_note: str | None = None,
    contradiction_resolved: bool = True,
    reviewed_at: datetime | None = REVIEWED_AT,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.StrategyRecommendationSpecialistOpinion(
        candidate_id=candidate_id,
        specialist_id=specialist_id,
        recommendation_status=recommendation_status,
        forecast_probability=forecast_probability,
        confidence=confidence,
        source_family=source_family,
        source_family_status=source_family_status,
        contradiction_note=contradiction_note,
        contradiction_resolved=contradiction_resolved,
        reviewed_at=reviewed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*opinions, **overrides):
    digest = module()
    values = {
        "generated_at": GENERATED_AT,
        "config_version": CONFIG_VERSION,
        "opinions": opinions,
    }
    values.update(overrides)
    return digest.build_strategy_recommendation_team_consensus_digest(**values)


def test_empty_input_returns_report_only_watch_summary() -> None:
    report = build_report()

    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.candidate_count == d("0")
    assert report.specialist_opinion_count == d("0")
    assert report.clear_candidate_count == d("0")
    assert report.watch_candidate_count == d("0")
    assert report.blocked_candidate_count == d("0")
    assert report.consensus_candidate_count == d("0")
    assert report.consensus_candidate_ratio is None
    assert report.status == "watch"
    assert report.reason_codes == ("empty_specialist_opinions",)
    assert report.rows == ()
    assert report.reason_rollups == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_aligned_specialists_build_confidence_weighted_consensus() -> None:
    report = build_report(
        opinion(
            "specialist-b",
            forecast_probability=d("0.620000"),
            confidence=d("0.750000"),
            source_family="official",
        ),
        opinion(
            "specialist-a",
            forecast_probability=d("0.580000"),
            confidence=d("0.250000"),
            source_family="model",
        ),
    )

    assert report.status == "clear"
    assert report.candidate_count == d("1")
    assert report.specialist_opinion_count == d("2")
    assert report.clear_candidate_count == d("1")
    assert report.consensus_candidate_count == d("1")
    assert report.consensus_candidate_ratio == d("1.000000")
    assert report.reason_codes == ("team_consensus_clear",)

    row = report.rows[0]
    assert row.candidate_id == "candidate-alpha"
    assert row.row_status == "clear"
    assert row.specialist_count == d("2")
    assert row.source_family_count == d("2")
    assert row.support_count == d("2")
    assert row.dissent_count == d("0")
    assert row.confidence_weighted_probability == d("0.610000")
    assert row.average_forecast_probability == d("0.600000")
    assert row.forecast_spread == d("0.040000")
    assert row.confidence_weighted_support_ratio == d("1.000000")
    assert row.reason_codes == ("team_consensus_clear",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_spread_family_disagreement_stale_dissent_and_notes_are_aggregated() -> None:
    stale_review = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)
    report = build_report(
        opinion(
            "macro",
            recommendation_status="support",
            forecast_probability=d("0.720000"),
            confidence=d("0.600000"),
            source_family="macro",
            source_family_status="aligned",
            reason_codes=("macro_tailwind", "shared_reason"),
        ),
        opinion(
            "news",
            recommendation_status="oppose",
            forecast_probability=d("0.410000"),
            confidence=d("0.300000"),
            source_family="news",
            source_family_status="conflict",
            contradiction_note="News desk flags unresolved policy contradiction",
            contradiction_resolved=False,
            reviewed_at=stale_review,
            reason_codes=("shared_reason", "news_conflict"),
        ),
        opinion(
            "model",
            recommendation_status="abstain",
            forecast_probability=d("0.500000"),
            confidence=d("0.100000"),
            source_family="model",
            source_family_status="stale",
            reason_codes=("model_stale",),
        ),
        stale_dissent_seconds=d("86400.000000"),
    )

    assert report.status == "blocked"
    assert report.candidate_count == d("1")
    assert report.blocked_candidate_count == d("1")
    assert report.consensus_candidate_count == d("0")
    assert report.consensus_candidate_ratio == d("0.000000")
    assert report.reason_codes == (
        "specialist_forecast_spread",
        "source_family_disagreement",
        "stale_dissent",
        "unresolved_contradiction_note",
        "macro_tailwind",
        "model_stale",
        "news_conflict",
        "shared_reason",
    )

    row = report.rows[0]
    assert row.row_status == "blocked"
    assert row.specialist_count == d("3")
    assert row.source_family_count == d("3")
    assert row.support_count == d("1")
    assert row.oppose_count == d("1")
    assert row.abstain_count == d("1")
    assert row.dissent_count == d("2")
    assert row.stale_dissent_count == d("1")
    assert row.unresolved_contradiction_count == d("1")
    assert row.confidence_weighted_probability == d("0.605000")
    assert row.confidence_weighted_support_ratio == d("0.600000")
    assert row.forecast_spread == d("0.310000")
    assert row.source_family_disagreement is True
    assert row.unresolved_contradiction_notes == (
        "News desk flags unresolved policy contradiction",
    )
    assert row.reason_codes == report.reason_codes


def test_deterministic_row_sorting_and_reason_rollups() -> None:
    report = build_report(
        opinion(
            "zeta",
            candidate_id="candidate-z",
            forecast_probability=d("0.700000"),
            source_family="news",
        ),
        opinion(
            "alpha",
            candidate_id="candidate-a",
            recommendation_status="oppose",
            forecast_probability=d("0.300000"),
            source_family="news",
            source_family_status="conflict",
            contradiction_note="reviewer contradiction remains open",
            contradiction_resolved=False,
            reason_codes=("open_review",),
        ),
        opinion(
            "beta",
            candidate_id="candidate-a",
            recommendation_status="support",
            forecast_probability=d("0.800000"),
            source_family="model",
            reason_codes=("open_review", "supporting_model"),
        ),
    )

    assert tuple(row.candidate_id for row in report.rows) == ("candidate-a", "candidate-z")
    assert report.rows[0].row_status == "blocked"
    assert report.rows[1].row_status == "clear"
    assert tuple(rollup.reason_code for rollup in report.reason_rollups) == (
        "specialist_forecast_spread",
        "source_family_disagreement",
        "unresolved_contradiction_note",
        "open_review",
        "supporting_model",
    )
    assert tuple(rollup.candidate_count for rollup in report.reason_rollups) == (
        d("1"),
        d("1"),
        d("1"),
        d("1"),
        d("1"),
    )
    assert all(rollup.candidate_ratio == d("0.500000") for rollup in report.reason_rollups)


def test_json_payload_helper_uses_decimal_strings_iso_datetimes_and_no_floats() -> None:
    digest = module()
    report = build_report(
        opinion(
            "news",
            source_family="news",
            forecast_probability=d("0.620000"),
            confidence=d("0.500000"),
        ),
    )

    payload = digest.strategy_recommendation_team_consensus_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["confidence_weighted_probability"] == "0.620000"
    assert payload["rows"][0]["latest_reviewed_at"] == "2026-07-02T11:30:00+00:00"
    assert '"0.620000"' in encoded
    assert not any(isinstance(value, float) for value in _walk_values(payload))


def test_payload_helper_accepts_safe_dicts_and_rejects_phase_escape_values() -> None:
    digest = module()

    payload = digest.strategy_recommendation_team_consensus_digest_payload(
        {
            "generated_at": GENERATED_AT,
            "candidate_count": d("1.000000"),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(ValueError, match="candidate_count"):
        digest.strategy_recommendation_team_consensus_digest_payload(
            {
                "candidate_count": 1,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
        digest.strategy_recommendation_team_consensus_digest_payload(
            {
                "generated_at": datetime(2026, 7, 2, 12, 0),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        digest.strategy_recommendation_team_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": (
                    {
                        "paper_only": True,
                        "report_only": True,
                        "readonly": False,
                    },
                ),
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        digest.strategy_recommendation_team_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_address": "blocked",
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        digest.strategy_recommendation_team_consensus_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "summary": "wallet value must stay out of payloads",
            },
        )


def test_validation_rejects_bad_inputs_and_unsafe_flags() -> None:
    digest = module()

    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at="2026-07-02T12:00:00Z")
    with pytest.raises(ValueError, match="config_version"):
        build_report(config_version=" ")
    with pytest.raises(ValueError, match="opinions must be an iterable"):
        digest.build_strategy_recommendation_team_consensus_digest(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            opinions=object(),
        )
    with pytest.raises(ValueError, match="paper_only"):
        build_report(opinion("unsafe", paper_only=False))
    with pytest.raises(ValueError, match="forecast_probability"):
        opinion("float-probability", forecast_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence"):
        opinion("float-confidence", confidence=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reviewed_at"):
        opinion("naive-reviewed-at", reviewed_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="source_family_status"):
        opinion("bad-family-status", source_family_status="unknown")


def test_source_reason_codes_are_unique_and_deterministic() -> None:
    ranked = opinion(
        "ranked-reasons",
        reason_codes=("zeta_reason", "alpha_reason"),
    )

    assert ranked.reason_codes == ("alpha_reason", "zeta_reason")

    with pytest.raises(ValueError, match="reason_codes"):
        opinion("duplicate-reasons", reason_codes=("same_reason", "same_reason"))


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict() -> None:
    digest = module()

    class DecimalSubclass(Decimal):
        pass

    class StrSubclass(str):
        pass

    class DateTimeSubclass(datetime):
        pass

    assert digest.__all__ == (
        "StrategyRecommendationSpecialistOpinion",
        "StrategyRecommendationTeamConsensusDigestReport",
        "StrategyRecommendationTeamConsensusReasonRollup",
        "StrategyRecommendationTeamConsensusRow",
        "build_strategy_recommendation_team_consensus_digest",
        "strategy_recommendation_team_consensus_digest_payload",
    )
    for exported_name in digest.__all__:
        value = getattr(digest, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(opinion("frozen"))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].row_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="specialist_id"):
        opinion(StrSubclass("specialist-subclass"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=DecimalSubclass("1"))


def test_static_forbidden_surface_terms_are_absent() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "db",
        "database",
        "network",
        "request",
        "socket",
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "signing",
        "advice",
    ):
        assert forbidden not in lowered


def _walk_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value
