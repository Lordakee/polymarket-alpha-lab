from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_team_forecast_disagreement_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def aggregate(team_label: str, queue_label: str, **overrides: object):
    module = api()
    values = {
        "team_label": team_label,
        "queue_label": queue_label,
        "specialist_count": d("3"),
        "forecast_count": d("9"),
        "mean_forecast_probability": d("0.500000"),
        "median_forecast_probability": d("0.500000"),
        "high_forecast_probability": d("0.550000"),
        "low_forecast_probability": d("0.450000"),
        "latest_memory_refresh_at": GENERATED_AT - timedelta(seconds=3600),
        "covered_source_count": d("3"),
        "required_source_count": d("3"),
        "reviewers_available_count": d("1"),
        "review_items_waiting_count": d("0"),
        "escalation_urgency_score": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchTeamForecastDisagreementAggregate(**values)


def report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_forecast_disagreement_queue_report(
        items,
        config=cfg or module.ResearchTeamForecastDisagreementQueueConfig(),
        generated_at=generated_at,
    )


def test_queue_report_prioritizes_disagreement_freshness_coverage_capacity_and_escalation() -> None:
    module = api()
    blocked = aggregate(
        "macro-research",
        "policy-window",
        high_forecast_probability=d("0.850000"),
        low_forecast_probability=d("0.150000"),
        latest_memory_refresh_at=GENERATED_AT - timedelta(seconds=172800),
        covered_source_count=d("1"),
        required_source_count=d("4"),
        reviewers_available_count=d("1"),
        review_items_waiting_count=d("5"),
        escalation_urgency_score=d("0.900000"),
    )
    watch = aggregate(
        "event-research",
        "turnout-band",
        high_forecast_probability=d("0.650000"),
        low_forecast_probability=d("0.350000"),
        covered_source_count=d("2"),
        required_source_count=d("3"),
        reviewers_available_count=d("2"),
        review_items_waiting_count=d("3"),
        escalation_urgency_score=d("0.550000"),
    )
    passing = aggregate("ops-research", "baseline-band")

    queue = report(passing, blocked, watch)
    rebuilt = report(watch, passing, blocked)
    changed = report(
        passing,
        watch,
        aggregate(
            "macro-research",
            "policy-window",
            high_forecast_probability=d("0.800000"),
            low_forecast_probability=d("0.150000"),
            latest_memory_refresh_at=GENERATED_AT - timedelta(seconds=172800),
            covered_source_count=d("1"),
            required_source_count=d("4"),
            reviewers_available_count=d("1"),
            review_items_waiting_count=d("5"),
            escalation_urgency_score=d("0.900000"),
        ),
    )

    assert type(queue) is module.ResearchTeamForecastDisagreementQueueReport
    assert is_dataclass(queue)
    assert queue.queue_status == "block"
    assert queue.aggregate_count == d("3")
    assert queue.pass_count == d("1")
    assert queue.watch_count == d("1")
    assert queue.block_count == d("1")
    assert queue.max_disagreement_severity == d("0.700000")
    assert queue.max_memory_age_seconds == d("172800.000000")
    assert queue.min_source_coverage_ratio == d("0.250000")
    assert queue.min_review_capacity_ratio == d("0.200000")
    assert queue.max_escalation_urgency_score == d("0.900000")
    assert queue.reason_codes == (
        "disagreement_severity_block",
        "memory_refresh_stale",
        "source_coverage_block",
        "review_capacity_block",
        "escalation_urgency_block",
        "disagreement_severity_watch",
        "source_coverage_watch",
        "review_capacity_watch",
        "escalation_urgency_watch",
    )
    assert queue.paper_only is True
    assert queue.report_only is True
    assert queue.readonly is True

    assert tuple(row.queue_status for row in queue.rows) == ("block", "watch", "pass")
    assert queue.rows[0] == module.ResearchTeamForecastDisagreementQueueRow(
        team_label="macro-research",
        queue_label="policy-window",
        specialist_count=d("3"),
        forecast_count=d("9"),
        disagreement_severity=d("0.700000"),
        memory_age_seconds=d("172800.000000"),
        source_coverage_ratio=d("0.250000"),
        review_capacity_ratio=d("0.200000"),
        escalation_urgency_score=d("0.900000"),
        queue_status="block",
        reason_codes=(
            "disagreement_severity_block",
            "memory_refresh_stale",
            "source_coverage_block",
            "review_capacity_block",
            "escalation_urgency_block",
        ),
    )

    payload = module.research_team_forecast_disagreement_queue_report_payload(queue)
    assert payload == queue.payload
    assert payload["rows"][0]["disagreement_severity"] == "0.700000"
    assert payload["rows"][0]["memory_age_seconds"] == "172800.000000"
    assert payload["rows"][0]["source_coverage_ratio"] == "0.250000"
    assert payload["rows"][0]["review_capacity_ratio"] == "0.200000"
    assert payload["derived_validation_digest"] == queue.derived_validation_digest
    assert len(queue.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in queue.derived_validation_digest)
    assert queue.derived_validation_digest == rebuilt.derived_validation_digest
    assert queue.derived_validation_digest != changed.derived_validation_digest
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_queue_report_is_frozen_decimal_only_public_safe_and_readonly() -> None:
    module = api()
    queue = report(aggregate("ops-research", "baseline-band"))
    payload_text = repr(queue.payload).lower()

    assert module.DISAGREEMENT_QUEUE_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_FORECAST_DISAGREEMENT_QUEUE_REPORT_CONFIG_VERSION",
        "DISAGREEMENT_QUEUE_STATUSES",
        "REASON_CODES",
        "ResearchTeamForecastDisagreementAggregate",
        "ResearchTeamForecastDisagreementQueueConfig",
        "ResearchTeamForecastDisagreementQueueReport",
        "ResearchTeamForecastDisagreementQueueRow",
        "build_research_team_forecast_disagreement_queue_report",
        "research_team_forecast_disagreement_queue_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "account",
        "order",
        "private_key",
        "api_key",
        "secret",
        "recommend",
        "advice",
        "trade",
    ):
        assert forbidden not in payload_text

    with pytest.raises(FrozenInstanceError):
        queue.queue_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="specialist_count must be a Decimal"):
        aggregate("ops-research", "baseline-band", specialist_count=3)
    with pytest.raises(ValueError, match="specialist_count must be a whole Decimal"):
        aggregate("ops-research", "baseline-band", specialist_count=d("3.500000"))
    with pytest.raises(ValueError, match="mean_forecast_probability must be a Decimal"):
        aggregate(
            "ops-research",
            "baseline-band",
            mean_forecast_probability=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="latest_memory_refresh_at"):
        aggregate(
            "ops-research",
            "baseline-band",
            latest_memory_refresh_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="latest_memory_refresh_at"):
        aggregate(
            "ops-research",
            "baseline-band",
            latest_memory_refresh_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_label"):
        aggregate(_StringSubclass("ops-research"), "baseline-band")
    with pytest.raises(ValueError, match="public-safe"):
        aggregate("wallet", "baseline-band")
    with pytest.raises(ValueError, match="generated_at"):
        report(
            aggregate(
                "ops-research",
                "baseline-band",
                latest_memory_refresh_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.ResearchTeamForecastDisagreementQueueConfig(), paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(queue, derived_validation_digest="0" * 64)
    assert (
        report(
            aggregate("ops-research", "baseline-band"),
            generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        ).generated_at
        == GENERATED_AT
    )

    source = Path(
        "src/polymarket_alpha_lab/research_team_forecast_disagreement_queue_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "network",
        "wallet",
        "account",
        "auth",
        "private_key",
        "api_key",
        "secret",
        "clob",
        "submit",
        "cancel",
        "signing",
        "trade",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"__import__", "float", "open", "request", "write"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in {"connect", "execute", "write", "write_text"}


def _assert_no_floats(value: Any) -> None:
    assert not isinstance(value, float)
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)
