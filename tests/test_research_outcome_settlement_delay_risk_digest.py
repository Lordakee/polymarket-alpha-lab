from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_outcome_settlement_delay_risk_digest import (
    ResearchOutcomeSettlementDelayRiskConfig,
    ResearchOutcomeSettlementDelayRiskObservation,
    ResearchOutcomeSettlementDelayRiskReport,
    ResearchOutcomeSettlementDelayRiskRow,
    build_research_outcome_settlement_delay_risk_report,
    research_outcome_settlement_delay_risk_digest,
    research_outcome_settlement_delay_risk_report_payload,
    validate_research_outcome_settlement_delay_risk_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchOutcomeSettlementDelayRiskConfig:
    values = {
        "config_version": "research-outcome-settlement-delay-risk-digest-v0",
        "result_watch_after_seconds": d("3600.000000"),
        "result_block_after_seconds": d("21600.000000"),
        "settlement_watch_after_seconds": d("7200.000000"),
        "settlement_block_after_seconds": d("86400.000000"),
        "stale_observation_after_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return ResearchOutcomeSettlementDelayRiskConfig(**values)


def observation(
    index: int,
    *,
    private_candidate_id: str | None = None,
    private_event_id: str | None = None,
    private_event_slug: str | None = None,
    private_event_question: str | None = None,
    private_reference: str | None = None,
    private_locator: str | None = None,
    private_excerpt: str | None = None,
    observed_at: datetime | None = None,
    event_ended_at: datetime | None = None,
    result_confirmed_at: datetime | None = None,
    settlement_completed_at: datetime | None = None,
    manual_block: bool = False,
    hard_delay_flag: bool = False,
) -> ResearchOutcomeSettlementDelayRiskObservation:
    return ResearchOutcomeSettlementDelayRiskObservation(
        private_candidate_id=private_candidate_id or f"raw-candidate-{index:03d}",
        private_event_id=private_event_id or f"market-id-{index:03d}",
        private_event_slug=private_event_slug or f"market-slug-{index:03d}",
        private_event_question=private_event_question
        or f"Will private event {index:03d} resolve?",
        private_reference=private_reference,
        private_locator=private_locator,
        private_excerpt=private_excerpt,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=15),
        event_ended_at=event_ended_at or GENERATED_AT - timedelta(hours=2),
        result_confirmed_at=result_confirmed_at,
        settlement_completed_at=settlement_completed_at,
        manual_block=manual_block,
        hard_delay_flag=hard_delay_flag,
    )


def report(
    observations: tuple[ResearchOutcomeSettlementDelayRiskObservation, ...],
    *,
    cfg: ResearchOutcomeSettlementDelayRiskConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchOutcomeSettlementDelayRiskReport:
    return build_research_outcome_settlement_delay_risk_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_pass_watch_and_block_public_statuses_are_report_only() -> None:
    pass_report = report(
        (
            observation(
                1,
                event_ended_at=GENERATED_AT - timedelta(hours=2),
                result_confirmed_at=GENERATED_AT - timedelta(minutes=90),
                settlement_completed_at=GENERATED_AT - timedelta(minutes=45),
            ),
        ),
    )
    watch_report = report(
        (
            observation(
                2,
                event_ended_at=GENERATED_AT - timedelta(hours=2),
                result_confirmed_at=None,
                settlement_completed_at=None,
            ),
        ),
    )
    block_report = report(
        (
            observation(
                3,
                event_ended_at=GENERATED_AT - timedelta(hours=8),
                result_confirmed_at=None,
                settlement_completed_at=None,
            ),
        ),
    )

    assert pass_report.public_status == "pass"
    assert pass_report.rows[0].public_status == "pass"
    assert pass_report.pass_count == d("1.000000")
    assert pass_report.watch_count == d("0.000000")
    assert pass_report.block_count == d("0.000000")
    assert pass_report.reason_codes == ("settlement_delay_pass",)

    assert watch_report.public_status == "watch"
    assert watch_report.rows[0].public_status == "watch"
    assert watch_report.watch_count == d("1.000000")
    assert "result_confirmation_watch" in watch_report.rows[0].reason_codes

    assert block_report.public_status == "block"
    assert block_report.rows[0].public_status == "block"
    assert block_report.block_count == d("1.000000")
    assert "result_confirmation_block" in block_report.rows[0].reason_codes

    for payload in (
        research_outcome_settlement_delay_risk_report_payload(pass_report),
        research_outcome_settlement_delay_risk_report_payload(watch_report),
        research_outcome_settlement_delay_risk_report_payload(block_report),
    ):
        for key, value in _walk_payload_items(payload):
            if key.endswith("status") or key == "public_status":
                assert value in {"pass", "watch", "block"}


def test_decimal_type_datetime_type_and_frozen_dataclass_rejections() -> None:
    with pytest.raises(ValueError, match="result_watch_after_seconds"):
        config(result_watch_after_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="settlement_block_after_seconds"):
        config(settlement_block_after_seconds=_DecimalSubclass("86400.000000"))
    with pytest.raises(ValueError, match="stale_observation_after_seconds"):
        config(stale_observation_after_seconds=d("3600.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="event_ended_at"):
        observation(
            1,
            event_ended_at=_DatetimeSubclass(2026, 7, 8, 10, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="manual_block"):
        observation(1, manual_block=1)  # type: ignore[arg-type]

    delay_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        delay_report.public_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        delay_report.rows[0].result_delay_seconds = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="result_delay_seconds"):
        replace(
            delay_report.rows[0],
            result_delay_seconds=_DecimalSubclass("1.000000"),
        )


def test_public_payload_rejects_private_identifier_and_tracking_leaks() -> None:
    private_values = (
        "raw-candidate-secret-001",
        "market-id-secret-001",
        "market-slug-secret-001",
        "Will the secret event resolve?",
        "source-ref-secret-001",
        "https://private.example.invalid/secret",
        "raw source text secret should stay private",
    )
    delay_report = report(
        (
            observation(
                1,
                private_candidate_id=private_values[0],
                private_event_id=private_values[1],
                private_event_slug=private_values[2],
                private_event_question=private_values[3],
                private_reference=private_values[4],
                private_locator=private_values[5],
                private_excerpt=private_values[6],
                result_confirmed_at=GENERATED_AT - timedelta(minutes=90),
                settlement_completed_at=GENERATED_AT - timedelta(minutes=45),
            ),
        ),
    )

    payload = research_outcome_settlement_delay_risk_report_payload(delay_report)
    encoded = json.dumps(payload, sort_keys=True)

    for private_value in private_values:
        assert private_value not in encoded
    assert "private_candidate_id" not in encoded
    assert "market_id" not in encoded
    assert "market_slug" not in encoded
    assert "market_question" not in encoded
    assert "source_url" not in encoded
    assert validate_research_outcome_settlement_delay_risk_report_payload(payload) is True

    leaked_payloads = (
        {"candidate_id": "raw-candidate-secret-001"},
        {"rows": [{"market_slug": "market-slug-secret-001"}]},
        {"rows": [{"source_url": "https://private.example.invalid/secret"}]},
        {"public_status": "buy"},
        {"note": "connect wallet"},
    )
    for leaked_payload in leaked_payloads:
        with pytest.raises(ValueError):
            validate_research_outcome_settlement_delay_risk_report_payload(
                leaked_payload,
            )


def test_hard_flags_and_manual_hard_delay_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation(1), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(observation(1), readonly=False)

    manual_report = report((observation(1, manual_block=True),))
    hard_delay_report = report((observation(2, hard_delay_flag=True),))

    assert manual_report.public_status == "block"
    assert "manual_block" in manual_report.rows[0].reason_codes
    assert hard_delay_report.public_status == "block"
    assert "hard_delay_flag" in hard_delay_report.rows[0].reason_codes


def test_deterministic_payload_and_report_digest_consistency() -> None:
    observations = (
        observation(
            2,
            event_ended_at=GENERATED_AT - timedelta(hours=2),
            result_confirmed_at=None,
            settlement_completed_at=None,
        ),
        observation(
            1,
            event_ended_at=GENERATED_AT - timedelta(hours=2),
            result_confirmed_at=GENERATED_AT - timedelta(minutes=90),
            settlement_completed_at=GENERATED_AT - timedelta(minutes=45),
        ),
    )

    first_report = report(observations)
    second_report = report(tuple(reversed(observations)))
    first_payload = research_outcome_settlement_delay_risk_report_payload(first_report)
    second_payload = research_outcome_settlement_delay_risk_report_payload(second_report)

    assert first_payload == second_payload
    assert tuple(row.public_status for row in first_report.rows) == ("watch", "pass")
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert (
        first_payload["derived_validation_digest"]
        == first_report.derived_validation_digest
        == research_outcome_settlement_delay_risk_digest(first_report)
    )
    assert validate_research_outcome_settlement_delay_risk_report_payload(first_payload) is True

    tampered_payload = dict(first_payload)
    tampered_payload["watch_count"] = "0.000000"
    with pytest.raises(ValueError, match="digest"):
        validate_research_outcome_settlement_delay_risk_report_payload(tampered_payload)


def test_report_and_rows_validate_manual_consistency() -> None:
    delay_report = report((observation(1),))
    row = delay_report.rows[0]

    assert type(delay_report) is ResearchOutcomeSettlementDelayRiskReport
    assert type(row) is ResearchOutcomeSettlementDelayRiskRow
    with pytest.raises(ValueError, match="public_status"):
        replace(row, public_status="review")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("settlement_delay_pass", "manual_block"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(delay_report, pass_count=d("1.000000"))
    with pytest.raises(ValueError, match="public_status"):
        replace(delay_report, public_status="pass")


def test_owned_module_has_no_network_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_outcome_settlement_delay_risk_digest.py"
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
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommend",
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


def _walk_payload_items(value: object) -> tuple[tuple[str, object], ...]:
    items: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            items.append((key, item))
            items.extend(_walk_payload_items(item))
    elif isinstance(value, list):
        for item in value:
            items.extend(_walk_payload_items(item))
    return tuple(items)
