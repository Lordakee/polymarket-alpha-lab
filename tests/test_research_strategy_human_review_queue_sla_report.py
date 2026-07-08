from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_human_review_queue_sla_report.py",
)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_strategy_human_review_queue_sla_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def queue_input(**overrides: object):
    module = api()
    values = {
        "review_bucket": "macro_review_pass",
        "review_stage": "evidence_ready",
        "review_item_count": d("2.000000"),
        "max_review_age_seconds": d("1800.000000"),
        "average_review_age_seconds": d("1200.000000"),
        "evidence_urgency_score": d("0.200000"),
        "settlement_risk_pressure": d("0.100000"),
        "queue_capacity_available": d("4.000000"),
        "queue_capacity_required": d("2.000000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("human_review_queue_inputs_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyHumanReviewQueueSlaInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_human_review_queue_sla_report(
        items,
        config=cfg
        if cfg is not None
        else module.ResearchStrategyHumanReviewQueueSlaConfig(),
        generated_at=generated_at,
    )


def payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(payload_values(item))
        return tuple(values)
    return (value,)


def assert_no_numeric_scalars(value: Any) -> None:
    assert not any(type(item) in (int, float, Decimal) for item in payload_values(value))


def assert_no_private_public_surface(value: object) -> None:
    encoded = json.dumps(value, sort_keys=True).lower()
    forbidden_fragments = (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "condition_id",
        "slug",
        "question",
        "source_text",
        "raw_text",
        "source_url",
        "url",
        "://",
        "www.",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "sizing",
    )
    for fragment in forbidden_fragments:
        assert fragment not in encoded


def test_builds_pass_watch_and_block_queue_sla_rows() -> None:
    module = api()
    report = build_report(
        queue_input(),
        queue_input(
            review_bucket="macro_review_watch",
            max_review_age_seconds=d("8000.000000"),
            average_review_age_seconds=d("7200.000000"),
            evidence_urgency_score=d("0.700000"),
            settlement_risk_pressure=d("0.600000"),
            queue_capacity_available=d("5.000000"),
            queue_capacity_required=d("4.000000"),
        ),
        queue_input(
            review_bucket="macro_review_block",
            review_item_count=d("3.000000"),
            max_review_age_seconds=d("90000.000000"),
            average_review_age_seconds=d("64000.000000"),
            evidence_urgency_score=d("0.920000"),
            settlement_risk_pressure=d("0.860000"),
            queue_capacity_available=d("4.000000"),
            queue_capacity_required=d("6.000000"),
            observed_at=datetime(2026, 7, 8, 8, 30, tzinfo=timezone(timedelta(hours=-7))),
            reason_codes=("manual_review_queue_backlog_seen",),
        ),
    )

    assert type(report) is module.ResearchStrategyHumanReviewQueueSlaReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.report_status == "block"
    assert report.review_age_status == "block"
    assert report.evidence_urgency_status == "block"
    assert report.settlement_risk_status == "block"
    assert report.queue_capacity_status == "block"
    assert report.review_bucket_count == d("3.000000")
    assert report.review_item_count == d("7.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.max_review_age_seconds == d("90000.000000")
    assert report.average_review_age_seconds == d("24133.333333")
    assert report.max_evidence_urgency_score == d("0.920000")
    assert report.max_settlement_risk_pressure == d("0.860000")
    assert report.max_queue_capacity_utilization == d("1.000000")
    assert report.reason_codes == (
        "human_review_queue_sla_report_block",
        "review_age_block",
        "evidence_urgency_block",
        "settlement_risk_block",
        "queue_capacity_block",
        "review_age_watch",
        "evidence_urgency_watch",
        "settlement_risk_watch",
        "queue_capacity_watch",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.review_bucket == "macro_review_block"
    assert blocked.observed_at == datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
    assert blocked.queue_capacity_utilization == d("1.000000")
    assert blocked.reason_codes == (
        "manual_review_queue_backlog_seen",
        "review_age_block",
        "evidence_urgency_block",
        "settlement_risk_block",
        "queue_capacity_block",
    )
    assert watched.queue_capacity_utilization == d("0.800000")
    assert watched.reason_codes == (
        "human_review_queue_inputs_ready",
        "review_age_watch",
        "evidence_urgency_watch",
        "settlement_risk_watch",
        "queue_capacity_watch",
    )
    assert passed.reason_codes == (
        "human_review_queue_inputs_ready",
        "human_review_queue_sla_clear",
    )


def test_empty_public_payload_is_deterministic_safe_and_digest_validated() -> None:
    module = api()
    report = build_report()
    payload = module.research_strategy_human_review_queue_sla_report_payload(report)
    unsigned = {key: value for key, value in payload.items() if key != "derived_validation_digest"}
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert report.report_status == "block"
    assert report.review_bucket_count == ZERO
    assert report.review_item_count == ZERO
    assert report.reason_codes == ("human_review_queue_sla_no_inputs",)
    assert report.rows == ()
    assert payload == report.payload
    assert payload == module.research_strategy_human_review_queue_sla_report_payload(payload)
    assert payload["review_bucket_count"] == "0.000000"
    assert payload["derived_validation_digest"] == sha256(encoded.encode("utf-8")).hexdigest()
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert (
        module.research_strategy_human_review_queue_sla_report_digest(report)
        == report.derived_validation_digest
    )
    assert_no_numeric_scalars(payload)
    assert_no_private_public_surface(payload)

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_human_review_queue_sla_report_payload(tampered)

    unsafe_key = dict(payload)
    unsafe_key["market_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_strategy_human_review_queue_sla_report_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["reason_codes"] = ["wallet"]
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_strategy_human_review_queue_sla_report_payload(unsafe_value)

    numeric_leak = dict(payload)
    numeric_leak["review_bucket_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_human_review_queue_sla_report_payload(numeric_leak)


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    report = build_report(queue_input())

    assert module.STRATEGY_HUMAN_REVIEW_QUEUE_SLA_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REPORT_CONFIG_VERSION",
        "STRATEGY_HUMAN_REVIEW_QUEUE_SLA_STATUSES",
        "STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REASON_CODES",
        "ResearchStrategyHumanReviewQueueSlaConfig",
        "ResearchStrategyHumanReviewQueueSlaInput",
        "ResearchStrategyHumanReviewQueueSlaReasonCodeCount",
        "ResearchStrategyHumanReviewQueueSlaReport",
        "ResearchStrategyHumanReviewQueueSlaRow",
        "build_research_strategy_human_review_queue_sla_report",
        "research_strategy_human_review_queue_sla_report_digest",
        "research_strategy_human_review_queue_sla_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_review_age_seconds must be a Decimal"):
        queue_input(max_review_age_seconds=3600)
    with pytest.raises(ValueError, match="review_item_count must be a whole Decimal"):
        queue_input(review_item_count=d("1.500000"))
    with pytest.raises(ValueError, match="evidence_urgency_score must be a Decimal"):
        queue_input(evidence_urgency_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="settlement_risk_pressure"):
        queue_input(settlement_risk_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        queue_input(observed_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="observed_at"):
        queue_input(observed_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="review_bucket"):
        queue_input(review_bucket=_StringSubclass("macro_review"))
    with pytest.raises(ValueError, match="public-safe"):
        queue_input(review_bucket="market_slug")
    with pytest.raises(ValueError, match="observed_at"):
        build_report(queue_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="watch_review_age_seconds"):
        replace(
            module.ResearchStrategyHumanReviewQueueSlaConfig(),
            watch_review_age_seconds=d("90000.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.ResearchStrategyHumanReviewQueueSlaConfig(), paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    for value in (report, *report.rows, *report.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_seconds",
                    "_score",
                    "_pressure",
                    "_available",
                    "_required",
                    "_utilization",
                    "_ratio",
                ),
            ):
                assert type(item_value) is Decimal


def test_module_scope_has_no_external_action_or_private_payload_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
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
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "clob",
        "submit",
        "cancel",
        "signing",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "buy",
        "sell",
        "recommendation",
        "sizing",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_text",
        "source_url",
        "dsn",
        "table_name",
        "token",
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
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
