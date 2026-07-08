from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_watchlist_queue_rebalance_report import (
    DEFAULT_RESEARCH_STRATEGY_WATCHLIST_QUEUE_REBALANCE_CONFIG_VERSION,
    REBALANCE_STATUSES,
    ResearchStrategyWatchlistQueueEntry,
    ResearchStrategyWatchlistQueueRebalanceConfig,
    ResearchStrategyWatchlistQueueRebalanceItem,
    ResearchStrategyWatchlistQueueRebalanceReport,
    build_research_strategy_watchlist_queue_rebalance_report,
    research_strategy_watchlist_queue_rebalance_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_watchlist_queue_rebalance_report.py",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyWatchlistQueueRebalanceConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_WATCHLIST_QUEUE_REBALANCE_CONFIG_VERSION
        ),
        "watch_urgency_score": d("0.550000"),
        "block_urgency_score": d("0.850000"),
        "fresh_evidence_max_age_seconds": d("86400.000000"),
        "stale_evidence_age_seconds": d("259200.000000"),
        "watch_confidence_drift": d("0.100000"),
        "block_confidence_drift": d("0.250000"),
        "watch_cost_pressure": d("0.500000"),
        "block_cost_pressure": d("0.750000"),
        "watch_team_capacity": d("0.400000"),
        "block_team_capacity": d("0.150000"),
    }
    values.update(overrides)
    return ResearchStrategyWatchlistQueueRebalanceConfig(**values)


def entry(
    watchlist_key: str = "research-watchlist-alpha",
    *,
    urgency_score: Decimal = d("0.200000"),
    evidence_age_seconds: Decimal = d("3600.000000"),
    confidence_score_previous: Decimal = d("0.500000"),
    confidence_score_current: Decimal = d("0.520000"),
    cost_pressure_score: Decimal = d("0.200000"),
    team_capacity_score: Decimal = d("0.800000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyWatchlistQueueEntry:
    return ResearchStrategyWatchlistQueueEntry(
        watchlist_key=watchlist_key,
        urgency_score=urgency_score,
        evidence_age_seconds=evidence_age_seconds,
        confidence_score_previous=confidence_score_previous,
        confidence_score_current=confidence_score_current,
        cost_pressure_score=cost_pressure_score,
        team_capacity_score=team_capacity_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchStrategyWatchlistQueueEntry, ...],
    *,
    cfg: ResearchStrategyWatchlistQueueRebalanceConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyWatchlistQueueRebalanceReport:
    return build_research_strategy_watchlist_queue_rebalance_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if (
            field.name.endswith(
                (
                    "_count",
                    "_drift",
                    "_rank",
                    "_score",
                    "_seconds",
                ),
            )
            or "capacity" in field.name
        ):
            assert type(item) is Decimal


def test_watchlist_queue_rebalance_reduces_statuses_sorts_and_redacts_keys() -> None:
    summary = report(
        (
            entry(
                "research-watchlist-pass",
                urgency_score=d("0.200000"),
                evidence_age_seconds=d("3600.000000"),
                confidence_score_previous=d("0.500000"),
                confidence_score_current=d("0.520000"),
                cost_pressure_score=d("0.200000"),
                team_capacity_score=d("0.800000"),
            ),
            entry(
                "research-watchlist-block",
                urgency_score=d("0.900000"),
                evidence_age_seconds=d("300000.000000"),
                confidence_score_previous=d("0.350000"),
                confidence_score_current=d("0.750000"),
                cost_pressure_score=d("0.800000"),
                team_capacity_score=d("0.100000"),
            ),
            entry(
                "research-watchlist-watch",
                urgency_score=d("0.600000"),
                evidence_age_seconds=d("90000.000000"),
                confidence_score_previous=d("0.400000"),
                confidence_score_current=d("0.520000"),
                cost_pressure_score=d("0.550000"),
                team_capacity_score=d("0.350000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_STRATEGY_WATCHLIST_QUEUE_REBALANCE_CONFIG_VERSION
    )
    assert summary.rebalance_status == "block"
    assert summary.next_step == "block_report_only_research_watchlist_rebalance"
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.capacity_limited_count == d("2.000000")
    assert summary.stale_evidence_count == d("2.000000")
    assert summary.high_confidence_drift_count == d("2.000000")
    assert summary.high_cost_pressure_count == d("2.000000")
    assert summary.max_rebalance_score == d("0.800000")
    assert summary.average_rebalance_score == d("0.458407")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.rebalance_status, row.rebalance_rank) for row in summary.rows) == (
        ("block", d("1.000000")),
        ("watch", d("2.000000")),
        ("pass", d("3.000000")),
    )

    blocked = summary.rows[0]
    assert blocked.public_item_digest != "research-watchlist-block"
    assert len(blocked.public_item_digest) == 64
    assert blocked.confidence_drift == d("0.400000")
    assert blocked.capacity_pressure_score == d("0.900000")
    assert blocked.rebalance_score == d("0.800000")
    assert blocked.queue_rebalance_step == "pause_until_research_capacity_recovers"
    assert blocked.reason_codes == (
        "research_strategy_watchlist_queue_rebalance_urgency_block",
        "research_strategy_watchlist_queue_rebalance_confidence_drift_block",
        "research_strategy_watchlist_queue_rebalance_cost_pressure_block",
        "research_strategy_watchlist_queue_rebalance_capacity_block",
        "research_strategy_watchlist_queue_rebalance_evidence_stale",
    )

    watched = summary.rows[1]
    assert watched.confidence_drift == d("0.120000")
    assert watched.rebalance_score == d("0.448444")
    assert watched.queue_rebalance_step == "refresh_evidence_then_reassess"
    assert watched.reason_codes == (
        "research_strategy_watchlist_queue_rebalance_urgency_watch",
        "research_strategy_watchlist_queue_rebalance_confidence_drift_watch",
        "research_strategy_watchlist_queue_rebalance_cost_pressure_watch",
        "research_strategy_watchlist_queue_rebalance_capacity_watch",
        "research_strategy_watchlist_queue_rebalance_evidence_refresh_due",
    )

    passed = summary.rows[2]
    assert passed.rebalance_score == d("0.126778")
    assert passed.queue_rebalance_step == "retain_report_only_watchlist_review"
    assert passed.reason_codes == (
        "research_strategy_watchlist_queue_rebalance_pass",
    )


def test_payload_digest_is_deterministic_public_safe_and_round_trips() -> None:
    rows = (
        entry(
            "research-watchlist-watch",
            urgency_score=d("0.600000"),
            evidence_age_seconds=d("90000.000000"),
            confidence_score_previous=d("0.400000"),
            confidence_score_current=d("0.520000"),
            cost_pressure_score=d("0.550000"),
            team_capacity_score=d("0.350000"),
        ),
        entry(
            "research-watchlist-block",
            urgency_score=d("0.900000"),
            evidence_age_seconds=d("300000.000000"),
            confidence_score_previous=d("0.350000"),
            confidence_score_current=d("0.750000"),
            cost_pressure_score=d("0.800000"),
            team_capacity_score=d("0.100000"),
        ),
    )
    forward = report(rows)
    reversed_order = report(tuple(reversed(rows)))

    payload = forward.payload
    assert payload == research_strategy_watchlist_queue_rebalance_report_payload(forward)
    assert payload == reversed_order.payload
    assert payload == research_strategy_watchlist_queue_rebalance_report_payload(payload)
    assert len(payload["derived_validation_digest"]) == 64
    assert json.dumps(payload, sort_keys=True)

    serialized = json.dumps(payload, sort_keys=True)
    assert "research-watchlist-block" not in serialized
    assert "research-watchlist-watch" not in serialized
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "url",
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "live_execution",
        "dsn",
        "token",
    ):
        assert forbidden not in serialized.lower()

    for value in walk_values(payload):
        assert not isinstance(value, Decimal)
        assert type(value) in {str, bool, list, dict}
    for item in payload["rows"]:
        assert set(item) == {
            "public_item_digest",
            "urgency_score",
            "evidence_age_seconds",
            "confidence_score_previous",
            "confidence_score_current",
            "confidence_drift",
            "cost_pressure_score",
            "team_capacity_score",
            "capacity_pressure_score",
            "rebalance_score",
            "rebalance_rank",
            "rebalance_status",
            "queue_rebalance_step",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        }

    tampered = dict(payload)
    tampered["rebalance_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_watchlist_queue_rebalance_report_payload(tampered)


def test_empty_report_is_pass_with_no_inputs_reason() -> None:
    summary = report(())

    assert summary.rebalance_status == "pass"
    assert summary.next_step == "retain_report_only_research_watchlist_rebalance"
    assert summary.input_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == (
        "research_strategy_watchlist_queue_rebalance_no_inputs",
    )
    assert summary.max_rebalance_score == d("0.000000")
    assert summary.average_rebalance_score == d("0.000000")
    assert summary.payload["derived_validation_digest"] == summary.derived_validation_digest


def test_dataclasses_are_frozen_and_numeric_fields_are_exact_decimals() -> None:
    cfg = config()
    row = entry()
    summary = report((row,), cfg=cfg)

    assert REBALANCE_STATUSES == frozenset(("pass", "watch", "block"))
    assert is_dataclass(cfg)
    assert is_dataclass(row)
    assert is_dataclass(summary)
    with pytest.raises(FrozenInstanceError):
        row.urgency_score = d("0.300000")  # type: ignore[misc]

    for value in (cfg, row, summary, *summary.rows):
        assert_decimal_numeric_fields(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    with pytest.raises(ValueError, match="urgency_score must be a Decimal"):
        entry(urgency_score=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must use six decimal places"):
        entry(urgency_score=d("0.2001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        entry(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        report((row,), cfg=cfg.__class__(paper_only=False))


def test_report_validates_statuses_digest_ordering_and_payload_safety() -> None:
    summary = report(
        (
            entry(
                "research-watchlist-watch",
                urgency_score=d("0.600000"),
                evidence_age_seconds=d("90000.000000"),
                confidence_score_previous=d("0.400000"),
                confidence_score_current=d("0.520000"),
                cost_pressure_score=d("0.550000"),
                team_capacity_score=d("0.350000"),
            ),
        ),
    )
    item = summary.rows[0]

    with pytest.raises(ValueError, match="rebalance_status"):
        ResearchStrategyWatchlistQueueRebalanceItem(
            public_item_digest=item.public_item_digest,
            urgency_score=item.urgency_score,
            evidence_age_seconds=item.evidence_age_seconds,
            confidence_score_previous=item.confidence_score_previous,
            confidence_score_current=item.confidence_score_current,
            confidence_drift=item.confidence_drift,
            cost_pressure_score=item.cost_pressure_score,
            team_capacity_score=item.team_capacity_score,
            capacity_pressure_score=item.capacity_pressure_score,
            rebalance_score=item.rebalance_score,
            rebalance_rank=item.rebalance_rank,
            rebalance_status="ready",
            queue_rebalance_step=item.queue_rebalance_step,
            reason_codes=item.reason_codes,
        )

    with pytest.raises(ValueError, match="deterministic sequence"):
        ResearchStrategyWatchlistQueueRebalanceReport(
            generated_at=summary.generated_at,
            config_version=summary.config_version,
            rebalance_status=summary.rebalance_status,
            next_step=summary.next_step,
            input_count=summary.input_count,
            pass_count=summary.pass_count,
            watch_count=summary.watch_count,
            block_count=summary.block_count,
            capacity_limited_count=summary.capacity_limited_count,
            stale_evidence_count=summary.stale_evidence_count,
            high_confidence_drift_count=summary.high_confidence_drift_count,
            high_cost_pressure_count=summary.high_cost_pressure_count,
            max_rebalance_score=summary.max_rebalance_score,
            average_rebalance_score=summary.average_rebalance_score,
            rows=(
                ResearchStrategyWatchlistQueueRebalanceItem(
                    public_item_digest=item.public_item_digest,
                    urgency_score=item.urgency_score,
                    evidence_age_seconds=item.evidence_age_seconds,
                    confidence_score_previous=item.confidence_score_previous,
                    confidence_score_current=item.confidence_score_current,
                    confidence_drift=item.confidence_drift,
                    cost_pressure_score=item.cost_pressure_score,
                    team_capacity_score=item.team_capacity_score,
                    capacity_pressure_score=item.capacity_pressure_score,
                    rebalance_score=item.rebalance_score,
                    rebalance_rank=d("2.000000"),
                    rebalance_status=item.rebalance_status,
                    queue_rebalance_step=item.queue_rebalance_step,
                    reason_codes=item.reason_codes,
                ),
            ),
            reason_codes=summary.reason_codes,
        )

    bad_payload = summary.payload
    bad_payload["rows"] = [
        {
            **bad_payload["rows"][0],
            "queue_rebalance_step": "send_wallet_order",
        },
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_strategy_watchlist_queue_rebalance_report_payload(bad_payload)


def test_module_is_pure_report_only_and_does_not_expose_raw_market_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imports: set[str] = set()
    called_names: set[str] = set()
    string_literals: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value)

    assert imports <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }
    assert not (called_names & {"open", "print", "connect", "request", "post", "put"})

    public_payload_strings = [
        literal
        for literal in string_literals
        if not literal.startswith("unsafe term:")
    ]
    combined = "\n".join(public_payload_strings).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "position_size",
        "wallet_order",
        "private_key",
        "live_execution",
    ):
        assert forbidden not in combined
