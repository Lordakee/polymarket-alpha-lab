from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=timezone(timedelta(hours=-4)))
OBSERVED_AT = datetime(2026, 7, 3, 20, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _UnknownOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_conflict_arbitration_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-team-conflict-arbitration-test-v0",
        "max_fresh_evidence_age_seconds": d("7200.000000"),
        "max_probability_dispersion": d("0.050000"),
        "min_historical_calibration": d("0.600000"),
    }
    values.update(overrides)
    return module.StrategyTeamConflictArbitrationConfig(**values)


def recommendation(
    recommendation_id: str,
    *,
    candidate_id: str = "event-candidate-alpha",
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    selected_side: str = "yes",
    paper_recommendation_status: str = "recommend",
    model_probability: Decimal = d("0.640000"),
    confidence: Decimal = d("0.860000"),
    evidence_observed_at: datetime = OBSERVED_AT,
    historical_calibration: Decimal = d("0.820000"),
    cost_adjusted_edge: Decimal = d("0.040000"),
    source_config_version: str = "team-recommendation-feed-v0",
    evidence_reference: str = "team-rollup",
):
    module = api()
    return module.StrategyTeamConflictRecommendation(
        recommendation_id=recommendation_id,
        candidate_id=candidate_id,
        team_id=team_id,
        category_id=category_id,
        selected_side=selected_side,
        paper_recommendation_status=paper_recommendation_status,
        model_probability=model_probability,
        confidence=confidence,
        evidence_observed_at=evidence_observed_at,
        historical_calibration=historical_calibration,
        cost_adjusted_edge=cost_adjusted_edge,
        source_config_version=source_config_version,
        evidence_reference=evidence_reference,
    )


def report(*rows: object, generated_at: datetime = GENERATED_AT, cfg: object | None = None):
    module = api()
    return module.build_strategy_team_conflict_arbitration_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for child in value.values():
            items.extend(walk(child))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(walk(child))
        return tuple(items)
    return (value,)


def test_empty_input_returns_clear_decimal_phase1_report() -> None:
    digest = report()

    assert is_dataclass(digest)
    assert digest.generated_at == datetime(2026, 7, 3, 22, 0, tzinfo=UTC)
    assert digest.config_version == "strategy-team-conflict-arbitration-test-v0"
    assert digest.status == "clear"
    assert digest.reason_codes == ("team_conflict_arbitration_digest_clear",)
    assert digest.input_count == d("0")
    assert digest.candidate_count == d("0")
    assert digest.paper_recommend_count == d("0")
    assert digest.paper_watch_count == d("0")
    assert digest.paper_defer_count == d("0")
    assert digest.max_conflict_severity == d("0")
    assert digest.conflicted_candidate_ratio == d("0.000000")
    assert digest.reason_code_counts == ()
    assert digest.decisions == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_arbitrates_conflicting_team_recommendations_for_same_candidate() -> None:
    digest = report(
        recommendation(
            "rec-lower-edge",
            team_id="macro_policy",
            category_id="macro.policy",
            selected_side="yes",
            model_probability=d("0.610000"),
            confidence=d("0.780000"),
            historical_calibration=d("0.790000"),
            cost_adjusted_edge=d("0.020000"),
        ),
        recommendation(
            "rec-winner",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            selected_side="yes",
            model_probability=d("0.660000"),
            confidence=d("0.880000"),
            historical_calibration=d("0.840000"),
            cost_adjusted_edge=d("0.055000"),
        ),
        recommendation(
            "rec-opposing-side",
            team_id="elections_us",
            category_id="politics.us",
            selected_side="no",
            model_probability=d("0.580000"),
            confidence=d("0.850000"),
            historical_calibration=d("0.810000"),
            cost_adjusted_edge=d("0.045000"),
        ),
    )

    assert digest.status == "watch"
    assert digest.input_count == d("3")
    assert digest.candidate_count == d("1")
    assert digest.paper_watch_count == d("1")
    assert digest.paper_recommend_count == d("0")
    assert digest.paper_defer_count == d("0")
    assert digest.max_conflict_severity == d("2")
    assert digest.conflicted_candidate_ratio == d("1.000000")
    assert digest.reason_codes == (
        "side_disagreement",
        "probability_dispersion_high",
        "paper_watch_conflict_arbitration",
    )
    assert digest.reason_code_counts == (
        ("side_disagreement", d("1")),
        ("probability_dispersion_high", d("1")),
        ("paper_watch_conflict_arbitration", d("1")),
    )

    decision = digest.decisions[0]
    assert decision.candidate_id == "event-candidate-alpha"
    assert decision.chosen_recommendation_id == "rec-winner"
    assert decision.team_id == "crypto_btc"
    assert decision.category_id == "finance.crypto.btc"
    assert decision.selected_side == "yes"
    assert decision.model_probability == d("0.660000")
    assert decision.confidence == d("0.880000")
    assert decision.evidence_freshness == "fresh"
    assert decision.evidence_age_seconds == d("5400.000000")
    assert decision.historical_calibration == d("0.840000")
    assert decision.cost_adjusted_edge == d("0.055000")
    assert decision.conflict_severity == d("2")
    assert decision.chosen_paper_recommendation_status == "paper_watch"
    assert decision.team_count == d("3")
    assert decision.side_count == d("2")
    assert decision.reason_codes == (
        "side_disagreement",
        "probability_dispersion_high",
        "paper_watch_conflict_arbitration",
    )


def test_defer_status_when_best_recommendation_has_stale_or_weak_inputs() -> None:
    digest = report(
        recommendation(
            "rec-negative-edge",
            candidate_id="event-candidate-beta",
            selected_side="yes",
            model_probability=d("0.520000"),
            confidence=d("0.700000"),
            evidence_observed_at=GENERATED_AT - timedelta(hours=5),
            historical_calibration=d("0.590000"),
            cost_adjusted_edge=d("-0.005000"),
        ),
        recommendation(
            "rec-watch",
            candidate_id="event-candidate-beta",
            team_id="macro_policy",
            category_id="macro.policy",
            selected_side="yes",
            paper_recommendation_status="watch",
            model_probability=d("0.550000"),
            confidence=d("0.720000"),
            evidence_observed_at=GENERATED_AT - timedelta(hours=3),
            historical_calibration=d("0.610000"),
            cost_adjusted_edge=d("0.010000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.paper_defer_count == d("1")
    assert digest.reason_codes == (
        "stale_evidence",
        "low_historical_calibration",
        "negative_cost_adjusted_edge",
        "paper_defer_conflict_arbitration",
    )
    decision = digest.decisions[0]
    assert decision.chosen_recommendation_id == "rec-negative-edge"
    assert decision.evidence_freshness == "stale"
    assert decision.historical_calibration == d("0.590000")
    assert decision.cost_adjusted_edge == d("-0.005000")
    assert decision.chosen_paper_recommendation_status == "paper_defer"
    assert decision.reason_codes == digest.reason_codes


def test_sorts_candidates_by_status_severity_edge_and_identifier() -> None:
    digest = report(
        recommendation(
            "rec-clear",
            candidate_id="candidate-clear-z",
            cost_adjusted_edge=d("0.030000"),
        ),
        recommendation(
            "rec-watch-a",
            candidate_id="candidate-watch-a",
            selected_side="yes",
            cost_adjusted_edge=d("0.040000"),
        ),
        recommendation(
            "rec-watch-b",
            candidate_id="candidate-watch-a",
            team_id="macro_policy",
            category_id="macro.policy",
            selected_side="no",
            cost_adjusted_edge=d("0.035000"),
        ),
        recommendation(
            "rec-blocked",
            candidate_id="candidate-blocked-a",
            evidence_observed_at=GENERATED_AT - timedelta(hours=4),
            historical_calibration=d("0.500000"),
            cost_adjusted_edge=d("-0.001000"),
        ),
    )

    assert tuple(decision.candidate_id for decision in digest.decisions) == (
        "candidate-blocked-a",
        "candidate-watch-a",
        "candidate-clear-z",
    )
    assert tuple(decision.chosen_paper_recommendation_status for decision in digest.decisions) == (
        "paper_defer",
        "paper_watch",
        "paper_recommend",
    )


def test_payload_redacts_sensitive_strings_and_uses_no_float_values() -> None:
    module = api()
    secret = "postgres://agent:super-secret-token@localhost/polymarket"
    source = recommendation("rec-redacted", evidence_reference=secret)

    digest = report(source)
    payload = module.strategy_team_conflict_arbitration_digest_payload(digest)

    assert source.evidence_reference == "<redacted-evidence-reference>"
    assert digest.decisions[0].evidence_reference == "<redacted-evidence-reference>"
    assert secret not in repr(source)
    assert secret not in repr(digest)
    assert payload["decisions"][0]["evidence_reference"] == "<redacted-evidence-reference>"
    assert payload["input_count"] == "1"
    assert payload["conflicted_candidate_ratio"] == "0.000000"
    assert payload["decisions"][0]["model_probability"] == "0.640000"
    assert not any(isinstance(value, float) for value in walk(payload))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_team_conflict_arbitration_digest_payload(object())


def test_payload_dict_path_rejects_unsafe_and_tampered_public_payloads() -> None:
    module = api()
    good = report(recommendation("rec-good"))
    payload = module.strategy_team_conflict_arbitration_digest_payload(good)

    assert module.strategy_team_conflict_arbitration_digest_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_team_conflict_arbitration_digest_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_team_conflict_arbitration_digest_payload(
            {**payload, "signed_order_payload": "forbidden"},
        )
    with pytest.raises(ValueError, match="sensitive string value|sensitive content"):
        module.strategy_team_conflict_arbitration_digest_payload(
            {
                **payload,
                "decisions": [
                    {**payload["decisions"][0], "team_id": "secret-token-team"},
                ],
            },
        )
    with pytest.raises(ValueError, match="Decimal-derived|string"):
        module.strategy_team_conflict_arbitration_digest_payload(
            {**payload, "candidate_count": 1},
        )
    with pytest.raises(ValueError, match="candidate_count must match decisions"):
        module.strategy_team_conflict_arbitration_digest_payload(
            {**payload, "candidate_count": "2"},
        )
    with pytest.raises(ValueError, match="reason_code_counts must match decisions"):
        module.strategy_team_conflict_arbitration_digest_payload(
            {**payload, "reason_code_counts": [["paper_recommend_conflict_arbitration", "2"]]},
        )


def test_rejects_sensitive_public_string_values_before_repr_or_payload() -> None:
    secret = "postgres://agent:super-secret-token@localhost/polymarket"

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="strategy-secret-token-v0")
    with pytest.raises(ValueError, match="recommendation_id"):
        recommendation("rec-private-key")
    with pytest.raises(ValueError, match="candidate_id"):
        recommendation("rec-safe", candidate_id="candidate-secret-token")
    with pytest.raises(ValueError, match="team_id"):
        recommendation("rec-safe", team_id="order_submitter")
    with pytest.raises(ValueError, match="category_id"):
        recommendation("rec-safe", category_id="finance.wallet")
    with pytest.raises(ValueError, match="source_config_version"):
        recommendation("rec-safe", source_config_version=secret)

    good = report(recommendation("rec-good"))
    with pytest.raises(ValueError, match="chosen_recommendation_id"):
        replace(good.decisions[0], chosen_recommendation_id="replace-token")


def test_validation_rejects_float_public_numbers_bad_times_duplicates_and_flags() -> None:
    module = api()
    good = report(recommendation("rec-good"))
    row = good.decisions[0]

    with pytest.raises(FrozenInstanceError):
        row.team_id = "other"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(good, paper_only=False)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(good, candidate_count=d("2"))
    with pytest.raises(ValueError, match="model_probability"):
        recommendation("rec-float", model_probability=0.64)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence"):
        recommendation("rec-decimal-subclass", confidence=_DecimalSubclass("0.86"))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        recommendation(
            "rec-datetime-subclass",
            evidence_observed_at=_DatetimeSubclass(2026, 7, 3, 20, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        recommendation(
            "rec-unknown-offset",
            evidence_observed_at=datetime(2026, 7, 3, 20, 30, tzinfo=_UnknownOffsetTZ()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(recommendation("rec-naive-generated"), generated_at=datetime(2026, 7, 3, 22, 0))
    with pytest.raises(ValueError, match="future"):
        report(
            recommendation(
                "rec-future-evidence",
                evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="duplicate recommendation_id"):
        report(recommendation("rec-dup"), recommendation("rec-dup"))
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_team_conflict_arbitration_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="max_probability_dispersion"):
        config(max_probability_dispersion=d("1.000001"))


def test_decision_count_fields_reject_fractional_decimal_values() -> None:
    good = report(recommendation("rec-good"))
    row = good.decisions[0]

    with pytest.raises(ValueError, match="conflict_severity"):
        replace(row, conflict_severity=d("0.4"))
    with pytest.raises(ValueError, match="team_count"):
        replace(row, team_count=d("1.5"))
    with pytest.raises(ValueError, match="side_count"):
        replace(row, side_count=d("1.5"))


def test_reducer_module_has_no_io_or_live_trading_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_team_conflict_arbitration_digest.py"
    )
    tree = ast.parse(source_path.read_text())
    imported_modules = {
        alias.name.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules |= {
        (node.module or "").partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    assert not (
        imported_modules
        & {
            "asyncpg",
            "httpx",
            "os",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
        }
    )

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "get",
        "post",
        "put",
        "delete",
        "submit_order",
        "cancel_order",
        "sign",
    }
    call_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    call_names |= {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not (call_names & forbidden_calls)
