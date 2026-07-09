from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_team_signal_quality_decay_report import (
    DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_STATUSES,
    ResearchStrategyTeamSignalQualityDecayConfig,
    ResearchStrategyTeamSignalQualityDecayInput,
    ResearchStrategyTeamSignalQualityDecayReport,
    ResearchStrategyTeamSignalQualityDecayRow,
    build_research_strategy_team_signal_quality_decay_report,
    research_strategy_team_signal_quality_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyTeamSignalQualityDecayConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_REPORT_CONFIG_VERSION
        ),
        "fresh_signal_age_seconds": d("1800.000000"),
        "stale_signal_age_seconds": d("7200.000000"),
        "watch_quality_drop": d("0.100000"),
        "block_quality_drop": d("0.250000"),
        "min_pass_current_quality_score": d("0.700000"),
        "min_watch_current_quality_score": d("0.500000"),
        "min_pass_decay_adjusted_quality_score": d("0.650000"),
        "min_watch_decay_adjusted_quality_score": d("0.450000"),
        "max_pass_decay_pressure_score": d("0.200000"),
        "max_watch_decay_pressure_score": d("0.450000"),
        "min_pass_evidence_freshness_score": d("0.700000"),
        "min_watch_evidence_freshness_score": d("0.500000"),
        "min_pass_calibration_score": d("0.700000"),
        "min_watch_calibration_score": d("0.500000"),
        "max_pass_disagreement_pressure": d("0.150000"),
        "max_watch_disagreement_pressure": d("0.350000"),
        "max_pass_review_latency_pressure": d("0.200000"),
        "max_watch_review_latency_pressure": d("0.400000"),
    }
    values.update(overrides)
    return ResearchStrategyTeamSignalQualityDecayConfig(**values)


def signal_input(**overrides: object) -> ResearchStrategyTeamSignalQualityDecayInput:
    values = {
        "signal_ref": "team-signal-alpha",
        "observed_at": GENERATED_AT - timedelta(seconds=600),
        "baseline_quality_score": d("0.900000"),
        "current_quality_score": d("0.880000"),
        "baseline_confidence_score": d("0.900000"),
        "current_confidence_score": d("0.880000"),
        "evidence_freshness_score": d("0.900000"),
        "calibration_score": d("0.900000"),
        "disagreement_pressure": d("0.050000"),
        "review_latency_pressure": d("0.050000"),
    }
    values.update(overrides)
    return ResearchStrategyTeamSignalQualityDecayInput(**values)


def report(
    *rows: ResearchStrategyTeamSignalQualityDecayInput,
    cfg: ResearchStrategyTeamSignalQualityDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyTeamSignalQualityDecayReport:
    return build_research_strategy_team_signal_quality_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_scores_signal_quality_decay_and_rolls_up_status() -> None:
    summary = report(
        signal_input(),
        signal_input(
            signal_ref="team-signal-beta",
            observed_at=GENERATED_AT - timedelta(seconds=4500),
            baseline_quality_score=d("0.850000"),
            current_quality_score=d("0.720000"),
            baseline_confidence_score=d("0.800000"),
            current_confidence_score=d("0.700000"),
            evidence_freshness_score=d("0.600000"),
            calibration_score=d("0.600000"),
            disagreement_pressure=d("0.250000"),
            review_latency_pressure=d("0.300000"),
        ),
        signal_input(
            signal_ref="team-signal-gamma",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            baseline_quality_score=d("0.850000"),
            current_quality_score=d("0.420000"),
            baseline_confidence_score=d("0.800000"),
            current_confidence_score=d("0.300000"),
            evidence_freshness_score=d("0.350000"),
            calibration_score=d("0.400000"),
            disagreement_pressure=d("0.600000"),
            review_latency_pressure=d("0.700000"),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_REPORT_CONFIG_VERSION
    )
    assert summary.row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_quality_drop == d("0.193333")
    assert summary.mean_decay_pressure_score == d("0.328571")
    assert summary.mean_decay_adjusted_quality_score == d("0.498172")
    assert summary.lowest_decay_adjusted_quality_score == d("0.151200")
    assert summary.highest_quality_drop == d("0.430000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "signal_quality_decay_block",
        "quality_drop_review",
        "current_quality_review",
        "evidence_freshness_review",
        "calibration_review",
        "disagreement_pressure_review",
        "review_latency_review",
        "decay_pressure_review",
        "adjusted_quality_review",
        "signal_age_review",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyTeamSignalQualityDecayRow)
    assert blocked.aggregate_row_number == d("1.000000")
    assert len(blocked.signal_hash) == 64
    assert blocked.signal_age_seconds == d("7200.000000")
    assert blocked.signal_age_pressure == d("1.000000")
    assert blocked.quality_drop == d("0.430000")
    assert blocked.confidence_drop == d("0.500000")
    assert blocked.decay_pressure_score == d("0.640000")
    assert blocked.decay_adjusted_quality_score == d("0.151200")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "adjusted_quality_block",
        "calibration_block",
        "current_quality_block",
        "decay_pressure_block",
        "disagreement_pressure_block",
        "evidence_freshness_block",
        "quality_drop_block",
        "review_latency_block",
        "signal_age_block",
    )

    watched = summary.rows[1]
    assert watched.aggregate_row_number == d("2.000000")
    assert watched.signal_age_pressure == d("0.500000")
    assert watched.quality_drop == d("0.130000")
    assert watched.confidence_drop == d("0.100000")
    assert watched.decay_pressure_score == d("0.297143")
    assert watched.decay_adjusted_quality_score == d("0.506057")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "adjusted_quality_watch",
        "calibration_watch",
        "decay_pressure_watch",
        "disagreement_pressure_watch",
        "evidence_freshness_watch",
        "quality_drop_watch",
        "review_latency_watch",
        "signal_age_watch",
    )

    passed = summary.rows[2]
    assert passed.aggregate_row_number == d("3.000000")
    assert passed.signal_age_pressure == d("0.000000")
    assert passed.quality_drop == d("0.020000")
    assert passed.confidence_drop == d("0.020000")
    assert passed.decay_pressure_score == d("0.048571")
    assert passed.decay_adjusted_quality_score == d("0.837258")
    assert passed.status == "pass"
    assert passed.reason_codes == ("signal_quality_decay_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True
    assert len(passed.derived_validation_digest) == 64


def test_public_payload_is_deterministic_hashed_decimal_and_digest_guarded() -> None:
    sensitive_ref = (
        "candidate-alpha market-alpha will resolve "
        "https://private.example/path?api_key=hidden-token table=db.events"
    )
    first_payload = research_strategy_team_signal_quality_decay_report_payload(
        report(signal_input(signal_ref=sensitive_ref)),
    )
    second_payload = research_strategy_team_signal_quality_decay_report_payload(
        report(signal_input(signal_ref=sensitive_ref)),
    )
    encoded = json.dumps(first_payload, sort_keys=True).lower()

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["row_count"] == "1.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["signal_hash"]) == 64
    assert first_payload["rows"][0]["decay_adjusted_quality_score"] == "0.837258"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert first_payload["derived_validation_digest"] == _payload_digest(first_payload)
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
        "signal_ref",
    )
    assert all(fragment not in encoded for fragment in forbidden_payload_fragments)

    tampered_payload = json.loads(json.dumps(first_payload))
    tampered_payload["rows"][0]["decay_adjusted_quality_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_team_signal_quality_decay_report_payload(tampered_payload)

    numeric_payload = json.loads(json.dumps(first_payload))
    numeric_payload["row_count"] = 1
    with pytest.raises(ValueError, match="row_count"):
        research_strategy_team_signal_quality_decay_report_payload(numeric_payload)

    unsafe_payload = json.loads(json.dumps(first_payload))
    unsafe_payload["candidate_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_team_signal_quality_decay_report_payload(unsafe_payload)

    unsafe_nested_payload = json.loads(json.dumps(first_payload))
    unsafe_nested_payload["rows"][0]["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_team_signal_quality_decay_report_payload(unsafe_nested_payload)

    invalid_status_payload = json.loads(json.dumps(first_payload))
    invalid_status_payload["status"] = "execute"
    invalid_status_payload["derived_validation_digest"] = _payload_digest(
        invalid_status_payload,
    )
    with pytest.raises(ValueError, match="status"):
        research_strategy_team_signal_quality_decay_report_payload(
            invalid_status_payload,
        )

    invalid_row_status_payload = json.loads(json.dumps(first_payload))
    invalid_row_status_payload["rows"][0]["status"] = "execute"
    invalid_row_status_payload["derived_validation_digest"] = _payload_digest(
        invalid_row_status_payload,
    )
    with pytest.raises(ValueError, match="status"):
        research_strategy_team_signal_quality_decay_report_payload(
            invalid_row_status_payload,
        )

    execution_surface_payload = json.loads(json.dumps(first_payload))
    execution_surface_payload["execution_surface"] = "manual"
    execution_surface_payload["derived_validation_digest"] = _payload_digest(
        execution_surface_payload,
    )
    with pytest.raises(ValueError, match="execution|unexpected|unsafe"):
        research_strategy_team_signal_quality_decay_report_payload(
            execution_surface_payload,
        )


def test_validation_rejects_non_decimal_times_duplicates_flags_and_tampering() -> None:
    with pytest.raises(ValueError, match="baseline_quality_score"):
        signal_input(baseline_quality_score=0.9)
    with pytest.raises(ValueError, match="disagreement_pressure"):
        signal_input(disagreement_pressure=d("-0.1"))
    with pytest.raises(ValueError, match="observed_at"):
        signal_input(observed_at=datetime(2026, 7, 8, 11, 50))
    with pytest.raises(ValueError, match="generated_at"):
        report(signal_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report(signal_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate"):
        report(signal_input(signal_ref="same"), signal_input(signal_ref="same"))
    with pytest.raises(ValueError, match="threshold"):
        config(min_pass_current_quality_score=d("0.400000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="watch_quality_drop"):
        config(watch_quality_drop=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            signal_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )

    summary = report(signal_input())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary.rows[0],
            decay_adjusted_quality_score=d("0.500000"),
            derived_validation_digest=summary.rows[0].derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            row_count=d("0.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )


def test_public_dataclasses_are_frozen_and_module_has_no_forbidden_surfaces() -> None:
    summary = report(signal_input())
    row = summary.rows[0]

    assert is_dataclass(ResearchStrategyTeamSignalQualityDecayConfig)
    assert is_dataclass(ResearchStrategyTeamSignalQualityDecayInput)
    assert is_dataclass(ResearchStrategyTeamSignalQualityDecayRow)
    assert is_dataclass(ResearchStrategyTeamSignalQualityDecayReport)
    assert RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_STATUSES == (
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
        "src/polymarket_alpha_lab/research_strategy_team_signal_quality_decay_report.py",
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
            assert node.func.id != "float"

    assert summary.__class__.__module__.endswith(
        "research_strategy_team_signal_quality_decay_report",
    )


def _payload_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assert_no_decimal_or_raw_numeric_values(value: object) -> None:
    if type(value) is bool or value is None:
        return
    assert not isinstance(value, Decimal)
    assert type(value) is not int
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_raw_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_decimal_or_raw_numeric_values(item)
