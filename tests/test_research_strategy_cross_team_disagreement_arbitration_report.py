from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_cross_team_disagreement_arbitration_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api():
    return import_module(
        "polymarket_alpha_lab."
        "research_strategy_cross_team_disagreement_arbitration_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(disagreement_key: str = "alpha-disagreement", **overrides: object):
    module = api()
    values = {
        "disagreement_key": disagreement_key,
        "disagreement_severity_score": d("0.100000"),
        "evidence_maturity_score": d("0.950000"),
        "source_conflict_pressure_score": d("0.100000"),
        "specialist_lane_count": d("3.000000"),
        "required_specialist_lane_count": d("3.000000"),
        "queued_at": GENERATED_AT - timedelta(hours=1),
        "manual_escalation_urgency_score": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossTeamDisagreementArbitrationInput(**values)


def report(*values: object, config: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_cross_team_disagreement_arbitration_report(
        values,
        config=config or module.ResearchStrategyCrossTeamDisagreementArbitrationConfig(),
        generated_at=generated_at,
    )


def assert_public_numeric_payload(value: Any) -> None:
    assert not isinstance(value, float)
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for item_value in value.values():
            assert_public_numeric_payload(item_value)
    elif isinstance(value, list):
        for item_value in value:
            assert_public_numeric_payload(item_value)


def test_arbitration_report_rolls_up_readiness_axes_with_public_rows_and_digest() -> None:
    module = api()
    blocked = item(
        "blocked-disagreement",
        disagreement_severity_score=d("0.800000"),
        evidence_maturity_score=d("0.450000"),
        source_conflict_pressure_score=d("0.750000"),
        specialist_lane_count=d("1.000000"),
        queued_at=GENERATED_AT - timedelta(days=4),
        manual_escalation_urgency_score=d("0.900000"),
    )
    watched = item(
        "watched-disagreement",
        disagreement_severity_score=d("0.400000"),
        evidence_maturity_score=d("0.700000"),
        source_conflict_pressure_score=d("0.400000"),
        specialist_lane_count=d("2.000000"),
        queued_at=GENERATED_AT - timedelta(days=2),
        manual_escalation_urgency_score=d("0.550000"),
    )
    passing = item("passing-disagreement")

    readiness = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)
    changed = report(
        passing,
        watched,
        item(
            "blocked-disagreement",
            disagreement_severity_score=d("0.700000"),
            evidence_maturity_score=d("0.450000"),
            source_conflict_pressure_score=d("0.750000"),
            specialist_lane_count=d("1.000000"),
            queued_at=GENERATED_AT - timedelta(days=4),
            manual_escalation_urgency_score=d("0.900000"),
        ),
    )

    assert is_dataclass(readiness)
    assert readiness.status == "block"
    assert readiness.arbitration_count == d("3.000000")
    assert readiness.pass_count == d("1.000000")
    assert readiness.watch_count == d("1.000000")
    assert readiness.block_count == d("1.000000")
    assert readiness.disagreement_severity_watch_count == d("2.000000")
    assert readiness.low_evidence_maturity_count == d("2.000000")
    assert readiness.source_conflict_pressure_count == d("2.000000")
    assert readiness.specialist_lane_gap_count == d("2.000000")
    assert readiness.queue_age_watch_count == d("2.000000")
    assert readiness.manual_escalation_urgent_count == d("2.000000")
    assert readiness.max_disagreement_severity_score == d("0.800000")
    assert readiness.min_evidence_maturity_score == d("0.450000")
    assert readiness.max_source_conflict_pressure_score == d("0.750000")
    assert readiness.min_specialist_lane_coverage_score == d("0.333333")
    assert readiness.max_queue_age_seconds == d("345600.000000")
    assert readiness.max_manual_escalation_urgency_score == d("0.900000")
    assert readiness.reason_codes == (
        "cross_team_disagreement_arbitration_block",
        "disagreement_severity_block",
        "disagreement_severity_watch",
        "evidence_maturity_block",
        "evidence_maturity_watch",
        "manual_escalation_urgency_block",
        "manual_escalation_urgency_watch",
        "queue_age_block",
        "queue_age_watch",
        "source_conflict_pressure_block",
        "source_conflict_pressure_watch",
        "specialist_lane_coverage_block",
        "specialist_lane_coverage_watch",
    )
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    assert tuple(row.status for row in readiness.rows) == ("block", "watch", "pass")
    blocked_row = readiness.rows[0]
    assert blocked_row.aggregate_row_number == d("1.000000")
    assert blocked_row.aggregate_row_hash == hashlib.sha256(
        b"blocked-disagreement",
    ).hexdigest()
    assert blocked_row.specialist_lane_coverage_score == d("0.333333")
    assert blocked_row.queue_age_seconds == d("345600.000000")
    assert blocked_row.reason_codes == (
        "disagreement_severity_block",
        "evidence_maturity_block",
        "manual_escalation_urgency_block",
        "queue_age_block",
        "source_conflict_pressure_block",
        "specialist_lane_coverage_block",
    )
    assert not hasattr(blocked_row, "disagreement_key")

    payload = module.research_strategy_cross_team_disagreement_arbitration_report_payload(
        readiness,
    )
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["aggregate_row_hash"] == blocked_row.aggregate_row_hash
    assert "blocked-disagreement" not in json.dumps(payload, sort_keys=True)
    assert payload["public_digest"] == (
        module.research_strategy_cross_team_disagreement_arbitration_report_digest(
            readiness,
        )
    )
    assert len(payload["public_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["public_digest"])
    assert payload == (
        module.research_strategy_cross_team_disagreement_arbitration_report_payload(
            rebuilt,
        )
    )
    assert readiness.public_digest != changed.public_digest
    assert_public_numeric_payload(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    module = api()
    readiness = report()

    assert readiness.status == "block"
    assert readiness.arbitration_count == d("0.000000")
    assert readiness.pass_count == d("0.000000")
    assert readiness.watch_count == d("0.000000")
    assert readiness.block_count == d("0.000000")
    assert readiness.rows == ()
    assert readiness.reason_codes == (
        "cross_team_disagreement_arbitration_no_inputs",
    )
    assert readiness.reason_code_counts == (
        module.ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount(
            reason_code="cross_team_disagreement_arbitration_no_inputs",
            count=d("1.000000"),
        ),
    )


def test_report_is_frozen_decimal_only_flagged_safe_and_revalidated() -> None:
    module = api()
    readiness = report(item("frozen-disagreement"))

    assert module.ARBITRATION_READINESS_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_DISAGREEMENT_ARBITRATION_REPORT_CONFIG_VERSION",
        "ARBITRATION_READINESS_STATUSES",
        "ResearchStrategyCrossTeamDisagreementArbitrationConfig",
        "ResearchStrategyCrossTeamDisagreementArbitrationInput",
        "ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount",
        "ResearchStrategyCrossTeamDisagreementArbitrationReport",
        "ResearchStrategyCrossTeamDisagreementArbitrationRow",
        "build_research_strategy_cross_team_disagreement_arbitration_report",
        "research_strategy_cross_team_disagreement_arbitration_report_digest",
        "research_strategy_cross_team_disagreement_arbitration_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        readiness.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness.rows[0].manual_escalation_urgency_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        item("flagged-disagreement", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(module.ResearchStrategyCrossTeamDisagreementArbitrationConfig(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)
    with pytest.raises(ValueError, match="public_digest"):
        replace(readiness, public_digest="0" * 64)
    with pytest.raises(ValueError, match="arbitration_count"):
        replace(readiness, arbitration_count=d("9.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(readiness, status="watch")

    with pytest.raises(ValueError, match="disagreement_severity_score"):
        item("int-disagreement", disagreement_severity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_maturity_score"):
        item(
            "subclass-disagreement",
            evidence_maturity_score=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="specialist_lane_count"):
        item("fractional-lanes", specialist_lane_count=d("2.500000"))
    with pytest.raises(ValueError, match="required_specialist_lane_count"):
        item("zero-required-lanes", required_specialist_lane_count=d("0.000000"))
    with pytest.raises(ValueError, match="queued_at"):
        item("naive-time", queued_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="queued_at"):
        item("subclass-time", queued_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="queued_at"):
        item("none-offset-time", queued_at=datetime(2026, 7, 8, 11, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at"):
        report(item("future-queue", queued_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="generated_at"):
        report(item("naive-generated"), generated_at=datetime(2026, 7, 8, 12, 0))

    shifted = report(
        item(
            "shifted-time",
            queued_at=datetime(2026, 7, 8, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.rows[0].queued_at == datetime(2026, 7, 8, 11, 0, tzinfo=UTC)
    assert shifted.rows[0].queue_age_seconds == d("3600.000000")

    object.__setattr__(readiness.rows[0], "aggregate_row_hash", "source_url:https")
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_cross_team_disagreement_arbitration_report_payload(
            readiness,
        )


def test_static_forbidden_public_surfaces_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "position_size",
        "buy",
        "sell",
        "recommend",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"__import__", "float", "open", "request", "write"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in {
                    "connect",
                    "execute",
                    "write",
                    "write_bytes",
                    "write_text",
                }

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
