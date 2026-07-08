from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_signal_corroboration_queue_report import (
    ResearchStrategySignalCorroborationQueueConfig,
    ResearchStrategySignalCorroborationQueueInput,
    ResearchStrategySignalCorroborationQueueReasonCodeCount,
    ResearchStrategySignalCorroborationQueueReport,
    ResearchStrategySignalCorroborationQueueRow,
    build_research_strategy_signal_corroboration_queue_report,
    research_strategy_signal_corroboration_queue_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedSignalShape:
    public_signal_label: str
    aggregate_evidence_freshness: Decimal
    source_reliability: Decimal
    contradiction_pressure: Decimal
    team_confidence_dispersion: Decimal
    cost_input_quality: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    event_id: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategySignalCorroborationQueueConfig:
    values = {
        "config_version": "research-strategy-signal-corroboration-queue-v0",
        "fresh_evidence_score": d("0.800000"),
        "stale_evidence_score": d("0.400000"),
        "reliable_source_score": d("0.800000"),
        "low_source_score": d("0.400000"),
        "aligned_team_dispersion": d("0.200000"),
        "dispersed_team_threshold": d("0.600000"),
        "evidence_freshness_weight": d("0.250000"),
        "source_reliability_weight": d("0.250000"),
        "contradiction_pressure_weight": d("0.250000"),
        "team_confidence_dispersion_weight": d("0.150000"),
        "cost_input_quality_weight": d("0.100000"),
        "watch_queue_pressure": d("0.350000"),
        "block_queue_pressure": d("0.650000"),
        "block_contradiction_pressure": d("0.850000"),
        "min_cost_input_quality": d("0.300000"),
    }
    values.update(overrides)
    return ResearchStrategySignalCorroborationQueueConfig(**values)


def signal(
    public_signal_label: str,
    *,
    aggregate_evidence_freshness: Decimal = d("0.950000"),
    source_reliability: Decimal = d("0.920000"),
    contradiction_pressure: Decimal = d("0.100000"),
    team_confidence_dispersion: Decimal = d("0.120000"),
    cost_input_quality: Decimal = d("0.930000"),
    upstream_reason_codes: tuple[str, ...] = (),
) -> ResearchStrategySignalCorroborationQueueInput:
    return ResearchStrategySignalCorroborationQueueInput(
        public_signal_label=public_signal_label,
        aggregate_evidence_freshness=aggregate_evidence_freshness,
        source_reliability=source_reliability,
        contradiction_pressure=contradiction_pressure,
        team_confidence_dispersion=team_confidence_dispersion,
        cost_input_quality=cost_input_quality,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategySignalCorroborationQueueConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySignalCorroborationQueueReport:
    return build_research_strategy_signal_corroboration_queue_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_digest() -> None:
    queue_report = report(())
    payload = research_strategy_signal_corroboration_queue_report_payload(queue_report)

    assert type(queue_report) is ResearchStrategySignalCorroborationQueueReport
    assert queue_report.generated_at == GENERATED_AT
    assert queue_report.config_version == (
        "research-strategy-signal-corroboration-queue-v0"
    )
    assert queue_report.status == "block"
    assert queue_report.signal_count == d("0")
    assert queue_report.pass_count == d("0")
    assert queue_report.watch_count == d("0")
    assert queue_report.block_count == d("0")
    assert queue_report.average_queue_pressure_score is None
    assert queue_report.max_contradiction_pressure is None
    assert queue_report.min_cost_input_quality is None
    assert queue_report.rows == ()
    assert queue_report.reason_codes == ("no_signal_corroboration_inputs",)
    assert queue_report.reason_code_counts == (
        ResearchStrategySignalCorroborationQueueReasonCodeCount(
            reason_code="no_signal_corroboration_inputs",
            count=d("1"),
        ),
    )
    assert queue_report.paper_only is True
    assert queue_report.report_only is True
    assert queue_report.readonly is True
    assert payload["queue_digest"] == queue_report.queue_digest
    assert queue_report.queue_digest == _expected_digest(payload)


def test_queue_rows_rank_public_safe_signals_with_pass_watch_block_statuses() -> None:
    queue_report = report(
        (
            signal(
                "zeta-public-signal",
                aggregate_evidence_freshness=d("0.600000"),
                source_reliability=d("0.550000"),
                contradiction_pressure=d("0.400000"),
                team_confidence_dispersion=d("0.500000"),
                cost_input_quality=d("0.650000"),
                upstream_reason_codes=("manual_reviewed",),
            ),
            signal(
                "omega-public-signal",
                aggregate_evidence_freshness=d("0.700000"),
                source_reliability=d("0.500000"),
                contradiction_pressure=d("0.900000"),
                team_confidence_dispersion=d("0.300000"),
                cost_input_quality=d("0.200000"),
            ),
            signal("alpha-public-signal"),
        ),
    )

    assert queue_report.status == "block"
    assert queue_report.signal_count == d("3")
    assert queue_report.pass_count == d("1")
    assert queue_report.watch_count == d("1")
    assert queue_report.block_count == d("1")
    assert queue_report.average_queue_pressure_score == d("0.351667")
    assert queue_report.max_contradiction_pressure == d("0.900000")
    assert queue_report.min_cost_input_quality == d("0.200000")
    assert tuple(row.public_signal_label for row in queue_report.rows) == (
        "alpha-public-signal",
        "omega-public-signal",
        "zeta-public-signal",
    )

    passing, blocked, watched = queue_report.rows
    assert type(passing) is ResearchStrategySignalCorroborationQueueRow
    assert passing.queue_pressure_score == d("0.082500")
    assert passing.queue_status == "pass"
    assert passing.queue_action == "retain_public_summary"
    assert passing.reason_codes == (
        "contradiction_pressure_low",
        "cost_inputs_usable",
        "fresh_aggregate_evidence",
        "reliable_source_support",
        "signal_corroboration_pass",
        "team_confidence_aligned",
    )
    assert blocked.queue_pressure_score == d("0.550000")
    assert blocked.queue_status == "block"
    assert blocked.queue_action == "hold_for_public_corroboration"
    assert "contradiction_pressure_block" in blocked.reason_codes
    assert "cost_inputs_low_quality" in blocked.reason_codes
    assert watched.queue_pressure_score == d("0.422500")
    assert watched.queue_status == "watch"
    assert watched.queue_action == "queue_public_corroboration"
    assert "input_manual_reviewed" in watched.reason_codes
    assert set(queue_report.reason_codes) >= {
        "signal_corroboration_pass",
        "signal_corroboration_watch",
        "signal_corroboration_block",
    }


def test_payload_and_digest_are_deterministic_without_float_or_raw_ids() -> None:
    queue_report = report(
        (
            SuppliedSignalShape(
                public_signal_label="beta-public-signal",
                aggregate_evidence_freshness=d("0.820000"),
                source_reliability=d("0.810000"),
                contradiction_pressure=d("0.120000"),
                team_confidence_dispersion=d("0.190000"),
                cost_input_quality=d("0.900000"),
            ),
            signal("alpha-public-signal", upstream_reason_codes=("zeta", "alpha")),
        ),
    )

    payload = research_strategy_signal_corroboration_queue_report_payload(queue_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == research_strategy_signal_corroboration_queue_report_payload(
        queue_report,
    )
    assert tuple(row["public_signal_label"] for row in payload["rows"]) == (
        "alpha-public-signal",
        "beta-public-signal",
    )
    assert queue_report.queue_digest == _expected_digest(payload)
    assert payload["rows"][0]["aggregate_evidence_freshness"] == "0.950000"
    assert payload["rows"][0]["queue_pressure_score"] == "0.082500"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert all(
        token not in encoded.lower()
        for token in (
            "event_id",
            "market_id",
            "market_slug",
            "source_id",
            "source_reference",
            "buy",
            "sell",
            "recommend",
            "position_size",
        )
    )


def test_validation_rejects_bad_types_unsafe_surfaces_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="weights"):
        config(evidence_freshness_weight=d("0.100000"))
    with pytest.raises(ValueError, match="watch_queue_pressure"):
        config(watch_queue_pressure=0.35)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_queue_pressure"):
        config(block_queue_pressure=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((signal("alpha-public-signal"),), generated_at=datetime(2026, 7, 8, 14, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (signal("alpha-public-signal"),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 14, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_signal_label"):
        signal(" alpha-public-signal")
    with pytest.raises(ValueError, match="public_signal_label"):
        signal("event_id:123")
    with pytest.raises(ValueError, match="aggregate_evidence_freshness"):
        signal("alpha-public-signal", aggregate_evidence_freshness=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability"):
        signal("alpha-public-signal", source_reliability=d("1.100000"))
    with pytest.raises(ValueError, match="team_confidence_dispersion"):
        signal(
            "alpha-public-signal",
            team_confidence_dispersion=_DecimalSubclass("0.100000"),
        )
    with pytest.raises(ValueError, match="upstream_reason_codes"):
        signal("alpha-public-signal", upstream_reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal("alpha-public-signal"), paper_only=False)
    with pytest.raises(ValueError, match="raw identifier"):
        report(
            (
                SuppliedSignalShape(
                    public_signal_label="alpha-public-signal",
                    aggregate_evidence_freshness=d("0.900000"),
                    source_reliability=d("0.900000"),
                    contradiction_pressure=d("0.100000"),
                    team_confidence_dispersion=d("0.100000"),
                    cost_input_quality=d("0.900000"),
                    event_id="evt-123",
                ),
            ),
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    queue_report = report((signal("alpha-public-signal"),))

    with pytest.raises(FrozenInstanceError):
        queue_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        queue_report.rows[0].queue_pressure_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="queue_pressure_score"):
        replace(queue_report.rows[0], queue_pressure_score=d("0.999999"))
    with pytest.raises(ValueError, match="queue_status"):
        replace(queue_report.rows[0], queue_status="blocked")
    with pytest.raises(ValueError, match="queue_digest"):
        replace(queue_report, queue_digest="0" * 64)


def test_owned_module_has_no_io_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_signal_corroboration_queue_report.py"
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
        "sqlite",
        "sqlalchemy",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "position",
    )

    assert all(term not in source for term in forbidden_terms)


def _expected_digest(payload: dict[str, object]) -> str:
    without_digest = dict(payload)
    without_digest.pop("queue_digest")
    encoded = json.dumps(
        without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
