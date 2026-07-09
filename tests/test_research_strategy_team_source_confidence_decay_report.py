from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_team_source_confidence_decay_report import (
    ResearchStrategyTeamSourceConfidenceDecayConfig,
    ResearchStrategyTeamSourceConfidenceDecayInput,
    ResearchStrategyTeamSourceConfidenceDecayReport,
    ResearchStrategyTeamSourceConfidenceDecayRow,
    build_research_strategy_team_source_confidence_decay_report,
    research_strategy_team_source_confidence_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def config(**overrides: object) -> ResearchStrategyTeamSourceConfidenceDecayConfig:
    values = {
        "config_version": "research-strategy-team-source-confidence-decay-report-v0",
        "fresh_age_seconds": d("3600.000000"),
        "stale_age_seconds": d("86400.000000"),
        "pass_effective_confidence_score": d("0.700000"),
        "watch_effective_confidence_score": d("0.400000"),
        "age_weight": d("0.550000"),
        "base_confidence_weight": d("0.450000"),
        "low_sample_block_threshold": d("1.000000"),
    }
    values.update(overrides)
    return ResearchStrategyTeamSourceConfidenceDecayConfig(**values)


def source_input(
    index: int,
    *,
    source_family: str = "official",
    source_kind: str = "primary",
    team_role: str = "resolver",
    observed_at: datetime | None = None,
    base_confidence_score: Decimal = d("0.900000"),
    historical_success_count: Decimal = d("4.000000"),
    historical_miss_count: Decimal = d("1.000000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchStrategyTeamSourceConfidenceDecayInput:
    return ResearchStrategyTeamSourceConfidenceDecayInput(
        candidate_id=f"candidate-secret-{index}",
        market_id=f"market-secret-{index}",
        market_slug=f"market-slug-secret-{index}",
        market_question=f"Will hidden market {index} resolve?",
        source_url=f"https://example.com/source/{index}",
        source_text=f"raw text secret {index}",
        source_family=source_family,
        source_kind=source_kind,
        team_role=team_role,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        base_confidence_score=base_confidence_score,
        historical_success_count=historical_success_count,
        historical_miss_count=historical_miss_count,
        reason_codes=reason_codes,
    )


def build_report(
    rows: tuple[ResearchStrategyTeamSourceConfidenceDecayInput, ...],
    *,
    cfg: ResearchStrategyTeamSourceConfidenceDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyTeamSourceConfidenceDecayReport:
    return build_research_strategy_team_source_confidence_decay_report(
        rows,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_empty_input_returns_blocked_report_only_digest() -> None:
    report = build_report(())
    payload = research_strategy_team_source_confidence_decay_report_payload(report)

    assert type(report) is ResearchStrategyTeamSourceConfidenceDecayReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-strategy-team-source-confidence-decay-report-v0"
    assert report.status == "blocked"
    assert report.source_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.average_effective_confidence_score == d("0.000000")
    assert report.max_source_age_seconds == d("0.000000")
    assert report.reason_codes == ("no_sources",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert payload["derived_validation_digest"] == canonical_digest(payload)


def test_fresh_high_confidence_sources_pass_with_deterministic_ordering() -> None:
    report = build_report(
        (
            source_input(
                2,
                source_family="analysis",
                source_kind="secondary",
                team_role="reviewer",
                observed_at=GENERATED_AT - timedelta(hours=2),
                base_confidence_score=d("0.750000"),
                historical_success_count=d("6.000000"),
                historical_miss_count=d("2.000000"),
                reason_codes=("manual_reviewed",),
            ),
            source_input(
                1,
                source_family="official",
                source_kind="primary",
                team_role="resolver",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                base_confidence_score=d("0.900000"),
                historical_success_count=d("4.000000"),
                historical_miss_count=d("1.000000"),
            ),
        ),
    )

    assert report.status == "pass"
    assert report.source_count == d("2.000000")
    assert report.pass_count == d("2.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.average_effective_confidence_score == d("0.796980")
    assert report.max_source_age_seconds == d("7200.000000")
    assert report.reason_codes == ("source_confidence_decay_pass",)

    first, second = report.rows
    assert type(first) is ResearchStrategyTeamSourceConfidenceDecayRow
    assert first.source_public_key.startswith("sha256:")
    assert first.source_public_key != "candidate-secret-1"
    assert first.source_family == "official"
    assert first.source_kind == "primary"
    assert first.team_role == "resolver"
    assert first.source_age_seconds == d("1800.000000")
    assert first.age_confidence_score == d("0.979167")
    assert first.base_confidence_score == d("0.900000")
    assert first.track_record_score == d("0.800000")
    assert first.effective_confidence_score == d("0.855417")
    assert first.status == "pass"
    assert first.reason_codes == (
        "fresh_source",
        "source_confidence_decay_pass",
        "strong_track_record",
    )
    assert second.source_family == "analysis"
    assert second.effective_confidence_score == d("0.738542")
    assert second.reason_codes == (
        "fresh_source",
        "input_manual_reviewed",
        "source_confidence_decay_pass",
        "strong_track_record",
    )


def test_stale_low_sample_and_weak_track_record_block_source() -> None:
    report = build_report(
        (
            source_input(
                1,
                observed_at=GENERATED_AT - timedelta(days=2),
                base_confidence_score=d("0.500000"),
                historical_success_count=d("0.000000"),
                historical_miss_count=d("3.000000"),
                reason_codes=("needs_recheck",),
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "blocked"
    assert report.blocked_count == d("1.000000")
    assert report.average_effective_confidence_score == d("0.000000")
    assert row.source_age_seconds == d("172800.000000")
    assert row.age_confidence_score == d("0.000000")
    assert row.track_record_score == d("0.000000")
    assert row.effective_confidence_score == d("0.000000")
    assert row.status == "blocked"
    assert row.reason_codes == (
        "input_needs_recheck",
        "source_confidence_decay_blocked",
        "stale_source",
        "weak_track_record",
    )


def test_payload_is_json_ready_stable_and_excludes_sensitive_source_surfaces() -> None:
    raw = source_input(7, reason_codes=("zeta", "alpha"))
    report = build_report((raw,))
    payload = research_strategy_team_source_confidence_decay_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["effective_confidence_score"] == str(
        report.rows[0].effective_confidence_score,
    )
    assert payload["rows"][0]["reason_codes"] == [
        "fresh_source",
        "input_alpha",
        "input_zeta",
        "source_confidence_decay_pass",
        "strong_track_record",
    ]
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    for forbidden in (
        "candidate-secret-7",
        "market-secret-7",
        "market-slug-secret-7",
        "Will hidden market",
        "https://example.com",
        "raw text secret",
        "source_url",
        "source_text",
        "market_id",
        "market_slug",
        "market_question",
        "candidate_id",
    ):
        assert forbidden not in encoded


def test_public_payload_dict_is_schema_validated_and_digest_checked() -> None:
    payload = research_strategy_team_source_confidence_decay_report_payload(
        build_report((source_input(9),)),
    )

    assert research_strategy_team_source_confidence_decay_report_payload(payload) == payload

    unsafe_payload = dict(payload)
    unsafe_payload["source_url"] = "https://example.com/private-source"
    with pytest.raises(ValueError, match="payload schema"):
        research_strategy_team_source_confidence_decay_report_payload(unsafe_payload)

    tampered_payload = dict(payload)
    tampered_payload["source_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_team_source_confidence_decay_report_payload(tampered_payload)

    float_payload = dict(payload)
    float_payload["average_effective_confidence_score"] = 0.5
    with pytest.raises(ValueError, match="Decimal string"):
        research_strategy_team_source_confidence_decay_report_payload(float_payload)


def test_custom_threshold_config_builds_self_consistent_report() -> None:
    report = build_report(
        (source_input(1),),
        cfg=config(
            pass_effective_confidence_score=d("0.900000"),
            watch_effective_confidence_score=d("0.800000"),
        ),
    )

    assert report.status == "watch"
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("0.000000")
    assert report.rows[0].effective_confidence_score == d("0.855417")
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == (
        "fresh_source",
        "source_confidence_decay_watch",
    )
    payload = research_strategy_team_source_confidence_decay_report_payload(report)
    assert payload["derived_validation_digest"] == canonical_digest(payload)


def test_validation_rejects_bad_types_future_times_bad_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="age_weight"):
        config(age_weight=d("0.400000"))
    with pytest.raises(ValueError, match="pass_effective_confidence_score"):
        config(pass_effective_confidence_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="base_confidence_score"):
        source_input(1, base_confidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report((source_input(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            (source_input(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        source_input(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        build_report((source_input(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="source_family"):
        source_input(1, source_family="http://unsafe.example")
    with pytest.raises(ValueError, match="source_kind"):
        source_input(1, source_kind="websocket")
    with pytest.raises(ValueError, match="team_role"):
        source_input(1, team_role="wallet")
    with pytest.raises(ValueError, match="reason_codes"):
        source_input(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(source_input(1), paper_only=False)


def test_dataclasses_are_frozen_and_digest_rejects_tampering() -> None:
    report = build_report((source_input(1),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].effective_confidence_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="source_count"):
        replace(report, source_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="watch")


def test_owned_module_has_no_network_storage_wallet_order_or_recommendation_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_team_source_confidence_decay_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "dsn",
        "table",
        "token",
        "auth",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "candidate_id\":",
        "market_id\":",
        "market_slug\":",
        "market_question\":",
        "source_url\":",
        "source_text\":",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
