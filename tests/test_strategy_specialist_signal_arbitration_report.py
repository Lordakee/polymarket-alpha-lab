from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 40, tzinfo=UTC)
CONFIG_VERSION = "strategy-specialist-signal-arbitration-report-v0"
ZERO = Decimal("0.000000")


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_specialist_signal_arbitration_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    arbitration = module()
    values = {
        "config_version": CONFIG_VERSION,
        "evidence_quality_weight": d("0.300000"),
        "team_calibration_weight": d("0.250000"),
        "source_freshness_weight": d("0.200000"),
        "liquidity_confidence_weight": d("0.150000"),
        "conflict_severity_weight": d("0.100000"),
        "max_source_age_seconds": d("7200.000000"),
        "recommend_threshold": d("0.640000"),
        "caution_threshold": d("0.520000"),
        "block_conflict_severity": d("0.800000"),
    }
    values.update(overrides)
    return arbitration.StrategySpecialistSignalArbitrationConfig(**values)


def signal(
    team_id: str,
    *,
    candidate_id: str = "candidate-alpha",
    team_probability: Decimal = d("0.700000"),
    evidence_quality: Decimal = d("0.900000"),
    team_calibration: Decimal = d("0.850000"),
    liquidity_confidence: Decimal = d("0.750000"),
    conflict_severity: Decimal = d("0.100000"),
    observed_at: datetime = OBSERVED_AT,
    evidence_family: str = "model",
    reason_codes: tuple[str, ...] = ("specialist_signal_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    arbitration = module()
    return arbitration.StrategySpecialistSignalArbitrationInput(
        candidate_id=candidate_id,
        team_id=team_id,
        team_probability=team_probability,
        evidence_quality=evidence_quality,
        team_calibration=team_calibration,
        liquidity_confidence=liquidity_confidence,
        conflict_severity=conflict_severity,
        observed_at=observed_at,
        evidence_family=evidence_family,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals, cfg=None, generated_at: datetime = GENERATED_AT):
    arbitration = module()
    return arbitration.build_strategy_specialist_signal_arbitration_report(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_happy_path_arbitrates_weighted_specialist_signals() -> None:
    report = build_report(
        signal(
            "quality-team",
            team_probability=d("0.740000"),
            evidence_quality=d("0.900000"),
            team_calibration=d("0.800000"),
            liquidity_confidence=d("0.700000"),
            conflict_severity=d("0.100000"),
            observed_at=GENERATED_AT - timedelta(minutes=30),
            evidence_family="model",
            reason_codes=("specialist_signal_available", "quality_edge_supported"),
        ),
        signal(
            "calibrated-team",
            team_probability=d("0.610000"),
            evidence_quality=d("0.700000"),
            team_calibration=d("0.950000"),
            liquidity_confidence=d("0.900000"),
            conflict_severity=d("0.200000"),
            observed_at=GENERATED_AT - timedelta(minutes=60),
            evidence_family="research",
            reason_codes=("specialist_signal_available",),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.candidate_count == d("1.000000")
    assert report.signal_count == d("2.000000")
    assert report.recommend_count == d("1.000000")
    assert report.caution_count == ZERO
    assert report.blocked_count == ZERO
    assert report.status == "recommend"
    assert report.reason_codes == ("arbitration_recommend", "quality_edge_supported")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.candidate_id == "candidate-alpha"
    assert row.posture == "recommend"
    assert row.team_count == d("2.000000")
    assert row.weighted_probability == d("0.686304")
    assert row.weighted_evidence_quality == d("0.800000")
    assert row.weighted_team_calibration == d("0.875000")
    assert row.weighted_source_freshness == d("0.625000")
    assert row.weighted_liquidity_confidence == d("0.800000")
    assert row.weighted_conflict_severity == d("0.150000")
    assert row.arbitration_score == d("0.737527")
    assert row.conflict_adjusted_score == d("0.722527")
    assert row.probability_spread == d("0.130000")
    assert row.dominant_evidence_family == "model"
    assert row.reason_codes == ("arbitration_recommend", "quality_edge_supported")

    payload = module().strategy_specialist_signal_arbitration_report_payload(report)
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["weighted_probability"] == "0.686304"
    assert payload["rows"][0]["conflict_adjusted_score"] == "0.722527"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_conflict_and_stale_sources_drive_caution_and_blocked_postures() -> None:
    report = build_report(
        signal(
            "stale-team",
            candidate_id="candidate-caution",
            team_probability=d("0.570000"),
            evidence_quality=d("0.600000"),
            team_calibration=d("0.650000"),
            liquidity_confidence=d("0.550000"),
            conflict_severity=d("0.300000"),
            observed_at=GENERATED_AT - timedelta(hours=3),
        ),
        signal(
            "severe-conflict",
            candidate_id="candidate-blocked",
            team_probability=d("0.720000"),
            evidence_quality=d("0.950000"),
            team_calibration=d("0.900000"),
            liquidity_confidence=d("0.850000"),
            conflict_severity=d("0.850000"),
            observed_at=GENERATED_AT - timedelta(minutes=15),
            evidence_family="event",
        ),
    )

    assert report.status == "blocked"
    assert report.caution_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.reason_codes == (
        "arbitration_blocked",
        "conflict_severity_blocked",
        "source_freshness_watch",
    )
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-blocked",
        "candidate-caution",
    )
    blocked, caution = report.rows
    assert blocked.posture == "blocked"
    assert blocked.reason_codes == (
        "arbitration_blocked",
        "conflict_severity_blocked",
    )
    assert caution.posture == "caution"
    assert caution.weighted_source_freshness == ZERO
    assert caution.reason_codes == ("source_freshness_watch",)


def test_empty_input_returns_report_only_caution_summary() -> None:
    report = build_report()

    assert report.candidate_count == ZERO
    assert report.signal_count == ZERO
    assert report.status == "caution"
    assert report.reason_codes == ("empty_specialist_signals",)
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.derived_validation_digest


def test_digest_payload_rejects_tampering_and_flag_downgrades() -> None:
    report = build_report(signal("team-a"))
    payload = module().strategy_specialist_signal_arbitration_report_payload(report)

    tampered_score = dict(payload)
    tampered_score["recommend_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module().strategy_specialist_signal_arbitration_report_payload(tampered_score)

    tampered_digest = dict(payload)
    tampered_digest["derived_validation_digest"] = "not-the-derived-digest"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module().strategy_specialist_signal_arbitration_report_payload(tampered_digest)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module().strategy_specialist_signal_arbitration_report_payload(downgraded)


def test_frozen_dataclasses_decimal_only_and_validation_guards() -> None:
    arbitration = module()
    report = build_report(signal("team-a"))

    assert is_dataclass(arbitration.StrategySpecialistSignalArbitrationConfig)
    assert is_dataclass(arbitration.StrategySpecialistSignalArbitrationInput)
    assert is_dataclass(arbitration.StrategySpecialistSignalArbitrationRow)
    assert is_dataclass(arbitration.StrategySpecialistSignalArbitrationReasonCodeCount)
    assert is_dataclass(arbitration.StrategySpecialistSignalArbitrationReport)
    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].arbitration_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        signal("team-a", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="evidence_quality"):
        signal("team-a", evidence_quality=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="team_probability"):
        signal("team-a", team_probability=d("1.000001"))
    with pytest.raises(ValueError, match="observed_at"):
        signal("team-a", observed_at=datetime(2026, 7, 6, 11, 0))
    with pytest.raises(ValueError, match="max_source_age_seconds"):
        config(max_source_age_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="weight"):
        config(evidence_quality_weight=d("0.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            signal("future-team", observed_at=GENERATED_AT + timedelta(seconds=1)),
        )

    for item in (
        report,
        *report.rows,
        *report.reason_code_counts,
    ):
        for field_name, value in item.__dict__.items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field_name
            assert type(value) is not float, field_name


def test_rejects_unsafe_public_keys_and_values() -> None:
    arbitration = module()
    blocked_terms = tuple(
        "".join(parts)
        for parts in (
            ("li", "ve"),
            ("au", "th"),
            ("wa", "llet"),
            ("or", "der"),
            ("net", "work"),
            ("data", "base"),
            ("per", "sist"),
            ("sign", "ing"),
            ("mut", "ation"),
            ("b", "uy"),
            ("se", "ll"),
            ("tra", "de"),
        )
    )

    for term in blocked_terms:
        with pytest.raises(ValueError, match="unsafe"):
            arbitration.strategy_specialist_signal_arbitration_report_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    f"{term}_field": "blocked",
                },
            )
        with pytest.raises(ValueError, match="unsafe"):
            signal("team-a", reason_codes=(f"{term}_reason",))
        with pytest.raises(ValueError, match="unsafe"):
            signal("team-a", evidence_family=f"{term}_family")


def test_static_module_surface_is_decimal_only_and_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_specialist_signal_arbitration_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests.",
        "urllib",
        "sqlite",
        "psycopg",
        "subprocess",
        "socket",
        "open(",
        "private_key",
        "secret",
        "token",
        "api_key",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
    assert not re.search(r"\b(requests|urllib|sqlite|psycopg|socket)\b", lowered)


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
