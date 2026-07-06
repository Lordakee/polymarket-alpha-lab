from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import inspect

import pytest

from polymarket_alpha_lab import team_specialist_archetype_outcome_learning_score_v2 as score


GENERATED_AT = datetime(2026, 1, 15, 12, tzinfo=UTC)


def _observation(
    observation_id: str,
    *,
    specialist_id: str = "specialist-alpha",
    archetype: str = "macro_researcher",
    outcome_score: Decimal = Decimal("0.800000"),
    resolved_days_ago: int = 3,
    learning_days_ago: int | None = None,
) -> score.TeamSpecialistArchetypeOutcomeObservation:
    return score.TeamSpecialistArchetypeOutcomeObservation(
        observation_id=observation_id,
        specialist_id=specialist_id,
        archetype=archetype,
        evaluated_at=GENERATED_AT - timedelta(days=resolved_days_ago + 1),
        resolved_at=GENERATED_AT - timedelta(days=resolved_days_ago),
        outcome_score=outcome_score,
        learning_applied_at=(
            None
            if learning_days_ago is None
            else GENERATED_AT - timedelta(days=learning_days_ago)
        ),
        public_note="calibrated review",
    )


def _report(
    observations: tuple[score.TeamSpecialistArchetypeOutcomeObservation, ...],
) -> score.TeamSpecialistArchetypeOutcomeLearningScoreReport:
    return score.build_team_specialist_archetype_outcome_learning_score_v2_report(
        observations,
        generated_at=GENERATED_AT,
    )


def _walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        nested: list[object] = [value]
        for item in value.values():
            nested.extend(_walk(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = [value]
        for item in value:
            nested.extend(_walk(item))
        return tuple(nested)
    return (value,)


def test_archetype_outcome_learning_score_rolls_up_by_specialist_and_archetype() -> None:
    report = _report(
        (
            _observation(
                "obs-alpha-1",
                outcome_score=Decimal("0.800000"),
                learning_days_ago=1,
            ),
            _observation("obs-alpha-2", outcome_score=Decimal("0.900000")),
            _observation(
                "obs-beta-1",
                specialist_id="specialist-beta",
                archetype="policy_researcher",
                outcome_score=Decimal("0.700000"),
            ),
        ),
    )

    assert report.row_count == Decimal("2.000000")
    assert report.pass_count == Decimal("2.000000")
    assert report.status == "pass"
    alpha = report.rows[0]
    assert alpha.specialist_id == "specialist-alpha"
    assert alpha.archetype == "macro_researcher"
    assert alpha.observation_count == Decimal("2.000000")
    assert alpha.average_outcome_score == Decimal("0.850000")
    assert alpha.recent_learning_boost == Decimal("0.025000")
    assert alpha.archetype_outcome_learning_score == Decimal("0.875000")
    assert "positive_outcome_learning" in alpha.reason_codes


def test_poor_outcome_penalties_can_block_a_specialist_archetype() -> None:
    report = _report(
        (
            _observation("obs-poor-1", outcome_score=Decimal("0.200000")),
            _observation("obs-poor-2", outcome_score=Decimal("0.300000")),
        ),
    )

    row = report.rows[0]
    assert row.poor_outcome_count == Decimal("2.000000")
    assert row.poor_outcome_penalty == Decimal("0.250000")
    assert row.archetype_outcome_learning_score == Decimal("0.000000")
    assert row.learning_status == "blocked"
    assert report.status == "blocked"
    assert "poor_outcome_penalty" in row.reason_codes
    assert "outcome_learning_blocked" in row.reason_codes


def test_recent_learning_boost_can_lift_watch_score_to_pass() -> None:
    report = _report(
        (
            _observation(
                "obs-recent-1",
                outcome_score=Decimal("0.600000"),
                learning_days_ago=1,
            ),
        ),
    )

    row = report.rows[0]
    assert row.average_outcome_score == Decimal("0.600000")
    assert row.recent_learning_count == Decimal("1.000000")
    assert row.recent_learning_boost == Decimal("0.050000")
    assert row.archetype_outcome_learning_score == Decimal("0.650000")
    assert row.learning_status == "pass"
    assert "recent_learning_boost" in row.reason_codes


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    report = _report((_observation("obs-payload-1", learning_days_ago=1),))

    payload = score.team_specialist_archetype_outcome_learning_score_v2_payload(report)

    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["archetype_outcome_learning_score"] == "0.850000"
    assert score.team_specialist_archetype_outcome_learning_score_v2_payload(
        dict(payload),
    ) == payload
    for item in _walk(payload):
        assert not isinstance(item, Decimal)
        assert not isinstance(item, float)
        assert not (type(item) is int)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report((_observation("obs-frozen-1"),))

    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadObservation(score.TeamSpecialistArchetypeOutcomeObservation):
            pass

    with pytest.raises(TypeError):

        class BadReport(score.TeamSpecialistArchetypeOutcomeLearningScoreReport):
            pass


def test_hard_flags_are_required() -> None:
    report = _report((_observation("obs-flags-1"),))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(ValueError, match="paper_only"):
        score.TeamSpecialistArchetypeOutcomeLearningScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report((_observation("obs-digest-1"),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = score.team_specialist_archetype_outcome_learning_score_v2_payload(
        report,
    )
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest|row_count"):
        score.team_specialist_archetype_outcome_learning_score_v2_payload(
            tampered_payload,
        )


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    for unsafe_key in (
        "live_signal",
        "auth_token",
        "wallet_id",
        "order_hint",
        "network_path",
        "database_row",
        "persist_target",
        "signing_ref",
        "mutation_plan",
        "buy_side",
        "sell_side",
        "trade_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            score.TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem(
                key=unsafe_key,
                value="redacted",
            )

    for unsafe_value in (
        "live execution",
        "auth credential",
        "wallet detail",
        "order detail",
        "network endpoint",
        "database table",
        "persist record",
        "signing request",
        "mutation request",
        "buy instruction",
        "sell instruction",
        "trade instruction",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            score.TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem(
                key="safe_note",
                value=unsafe_value,
            )


def test_no_unsafe_public_surfaces_are_exported() -> None:
    unsafe_terms = (
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
    public_names = set(score.__all__)
    for public_name in public_names:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)
        public_value = getattr(score, public_name)
        if inspect.isclass(public_value) and hasattr(public_value, "__dataclass_fields__"):
            for field in fields(public_value):
                lowered_field = field.name.lower()
                assert not any(term in lowered_field for term in unsafe_terms)

    assert not any(
        public_name.startswith(("connect", "submit", "execute", "send", "store"))
        for public_name in public_names
    )
