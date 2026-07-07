from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 7, 15, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_event_catalyst_edge_confirmation_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    scorer = api()
    values = {
        "config_version": "strategy-candidate-event-catalyst-edge-confirmation-v2-v0",
        "minimum_catalyst_evidence_score": d("0.700000"),
        "minimum_probability_movement_attribution_score": d("0.700000"),
        "minimum_absolute_probability_move": d("0.020000"),
        "stale_source_age_seconds": d("3600.000000"),
        "maximum_contradiction_score": d("0.000000"),
        "minimum_cost_adjusted_margin": d("0.030000"),
        "watch_cost_adjusted_margin": d("0.010000"),
        "minimum_evidence_source_count": d("2"),
    }
    values.update(overrides)
    return scorer.StrategyCandidateEventCatalystEdgeConfirmationV2Config(**values)


def candidate(**overrides: object):
    scorer = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "event-market",
        "forecast_probability": d("0.640000"),
        "market_probability_before": d("0.500000"),
        "market_probability_after": d("0.550000"),
        "estimated_fee": d("0.010000"),
        "estimated_slippage": d("0.005000"),
        "catalyst_evidence_score": d("0.850000"),
        "probability_movement_attribution_score": d("0.900000"),
        "source_observed_at": GENERATED_AT - timedelta(minutes=20),
        "contradiction_score": d("0.000000"),
        "evidence_source_count": d("3"),
    }
    values.update(overrides)
    return scorer.StrategyCandidateEventCatalystEdgeConfirmationV2Input(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    scorer = api()
    return scorer.build_strategy_candidate_event_catalyst_edge_confirmation_v2_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)
        return
    assert type(value) is not float


def test_happy_path_confirms_candidate_edge_and_serializes_payload() -> None:
    scorer = api()
    digest_report = report(candidate())

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "strategy-candidate-event-catalyst-edge-confirmation-v2-v0"
    )
    assert digest_report.candidate_count == d("1")
    assert digest_report.pass_count == d("1")
    assert digest_report.watch_count == d("0")
    assert digest_report.blocked_count == d("0")
    assert digest_report.confirmed_count == d("1")
    assert digest_report.stale_source_count == d("0")
    assert digest_report.contradiction_blocked_count == d("0")
    assert digest_report.mean_cost_adjusted_margin == d("0.075000")
    assert digest_report.max_cost_adjusted_margin == d("0.075000")
    assert digest_report.min_cost_adjusted_margin == d("0.075000")
    assert digest_report.status == "pass"
    assert digest_report.reason_codes == (
        "candidate_event_catalyst_edge_confirmation_clear",
    )
    assert len(digest_report.digest) == 64
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    row = digest_report.rows[0]
    assert row.confirmation_status == "pass"
    assert row.raw_probability_move == d("0.050000")
    assert row.absolute_probability_move == d("0.050000")
    assert row.candidate_edge == d("0.090000")
    assert row.total_estimated_cost == d("0.015000")
    assert row.cost_adjusted_margin == d("0.075000")
    assert row.source_age_seconds == d("1200.000000")
    assert row.reason_codes == (
        "candidate_edge_positive",
        "catalyst_evidence_confirmed",
        "probability_movement_attributed",
        "source_fresh",
        "no_contradiction_detected",
        "cost_adjusted_margin_clear",
    )

    payload = scorer.strategy_candidate_event_catalyst_edge_confirmation_v2_payload(
        digest_report,
    )
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["cost_adjusted_margin"] == "0.075000"
    assert payload["rows"][0]["source_observed_at"] == "2026-07-07T14:40:00+00:00"
    assert payload["digest"] == digest_report.digest
    json.dumps(payload, sort_keys=True)
    assert_no_float(payload)


def test_quality_guards_emit_watch_and_blocked_reason_codes() -> None:
    digest_report = report(
        candidate(
            candidate_id="candidate-stale-watch",
            market_slug="watch-market",
            source_observed_at=GENERATED_AT - timedelta(hours=2),
            evidence_source_count=d("1"),
        ),
        candidate(
            candidate_id="candidate-blocked",
            market_slug="blocked-market",
            forecast_probability=d("0.530000"),
            market_probability_before=d("0.560000"),
            market_probability_after=d("0.520000"),
            estimated_fee=d("0.020000"),
            estimated_slippage=d("0.005000"),
            catalyst_evidence_score=d("0.400000"),
            probability_movement_attribution_score=d("0.500000"),
            contradiction_score=d("0.200000"),
            evidence_source_count=d("1"),
        ),
    )

    assert digest_report.status == "blocked"
    assert digest_report.pass_count == d("0")
    assert digest_report.watch_count == d("1")
    assert digest_report.blocked_count == d("1")
    assert digest_report.confirmed_count == d("0")
    assert digest_report.stale_source_count == d("1")
    assert digest_report.contradiction_blocked_count == d("1")
    assert digest_report.reason_codes == (
        "candidate_event_catalyst_edge_confirmation_blocked",
        "catalyst_evidence_score_blocked",
        "catalyst_source_count_low_watch",
        "contradiction_detected_blocked",
        "cost_adjusted_margin_blocked",
        "probability_movement_against_edge_blocked",
        "probability_movement_attribution_blocked",
        "source_stale_watch",
    )

    blocked, watched = digest_report.rows
    assert blocked.candidate_id == "candidate-blocked"
    assert blocked.confirmation_status == "blocked"
    assert blocked.raw_probability_move == d("-0.040000")
    assert blocked.candidate_edge == d("0.010000")
    assert blocked.cost_adjusted_margin == d("-0.015000")
    assert blocked.reason_codes == (
        "candidate_edge_positive",
        "catalyst_evidence_score_blocked",
        "probability_movement_attribution_blocked",
        "probability_movement_against_edge_blocked",
        "source_fresh",
        "contradiction_detected_blocked",
        "catalyst_source_count_low_watch",
        "cost_adjusted_margin_blocked",
    )

    assert watched.candidate_id == "candidate-stale-watch"
    assert watched.confirmation_status == "watch"
    assert watched.reason_codes == (
        "candidate_edge_positive",
        "catalyst_evidence_confirmed",
        "probability_movement_attributed",
        "source_stale_watch",
        "no_contradiction_detected",
        "catalyst_source_count_low_watch",
        "cost_adjusted_margin_clear",
    )


def test_digest_and_reason_code_counts_are_deterministic() -> None:
    alpha = candidate(candidate_id="alpha", market_slug="a-market")
    zeta = candidate(
        candidate_id="zeta",
        market_slug="z-market",
        source_observed_at=GENERATED_AT - timedelta(hours=2),
        evidence_source_count=d("1"),
    )

    first = report(zeta, alpha)
    second = report(alpha, zeta)

    assert first.digest == second.digest
    assert tuple(row.candidate_id for row in first.rows) == ("zeta", "alpha")
    assert tuple(row.candidate_id for row in second.rows) == ("zeta", "alpha")
    assert first.reason_code_counts == (
        ("candidate_edge_positive", d("2")),
        ("catalyst_evidence_confirmed", d("2")),
        ("cost_adjusted_margin_clear", d("2")),
        ("no_contradiction_detected", d("2")),
        ("probability_movement_attributed", d("2")),
        ("catalyst_source_count_low_watch", d("1")),
        ("source_fresh", d("1")),
        ("source_stale_watch", d("1")),
    )


def test_validation_rejects_non_decimal_inputs_flags_dates_and_inconsistency() -> None:
    scorer = api()
    digest_report = report(candidate())

    with pytest.raises(FrozenInstanceError):
        digest_report.rows[0].confirmation_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        candidate(forecast_probability=0.64)

    with pytest.raises(ValueError, match="forecast_probability must be exactly Decimal"):
        candidate(forecast_probability=_DecimalSubclass("0.640000"))

    with pytest.raises(ValueError, match="forecast_probability must be finite"):
        candidate(forecast_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(candidate(), generated_at="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            candidate(),
            generated_at=datetime(2026, 7, 7, 15, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        scorer.StrategyCandidateEventCatalystEdgeConfirmationV2Report(
            generated_at=_DatetimeSubclass(2026, 7, 7, 15, 0, tzinfo=UTC),
            config_version="strategy-candidate-event-catalyst-edge-confirmation-v2-v0",
            candidate_count=d("0"),
            pass_count=d("0"),
            watch_count=d("0"),
            blocked_count=d("0"),
            confirmed_count=d("0"),
            stale_source_count=d("0"),
            contradiction_blocked_count=d("0"),
            mean_cost_adjusted_margin=d("0.000000"),
            max_cost_adjusted_margin=d("0.000000"),
            min_cost_adjusted_margin=d("0.000000"),
            status="pass",
            reason_codes=("candidate_event_catalyst_edge_confirmation_clear",),
            reason_code_counts=(),
            digest="0" * 64,
            rows=(),
        )

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="input must be readonly"):
        candidate(readonly=False)

    with pytest.raises(ValueError, match="source_observed_at must not be after generated_at"):
        report(candidate(source_observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(
            candidate(candidate_id="dup", market_slug="same-market"),
            candidate(candidate_id="dup", market_slug="same-market"),
        )

    with pytest.raises(ValueError, match="watch_cost_adjusted_margin"):
        config(
            watch_cost_adjusted_margin=d("0.040000"),
            minimum_cost_adjusted_margin=d("0.030000"),
        )


def test_payload_rejects_dict_flag_downgrades_floats_and_unsafe_surface() -> None:
    scorer = api()

    with pytest.raises(ValueError, match="payload must be readonly"):
        scorer.strategy_candidate_event_catalyst_edge_confirmation_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        scorer.strategy_candidate_event_catalyst_edge_confirmation_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "cost_adjusted_margin": 0.1,
            },
        )

    with pytest.raises(ValueError, match="unsafe surface field"):
        scorer.strategy_candidate_event_catalyst_edge_confirmation_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_reference": "redacted",
            },
        )

    with pytest.raises(ValueError, match="sensitive value"):
        scorer.strategy_candidate_event_catalyst_edge_confirmation_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "public_note": "private catalyst feed",
            },
        )


def test_module_scope_has_no_live_surfaces_or_float_literals() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_event_catalyst_edge_confirmation_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "db",
        "open(",
        "order",
        "trade",
        "trading",
        "requests",
        "urllib",
        "http",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
