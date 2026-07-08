from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_cross_source_contradiction_resolution_queue_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_cross_source_contradiction_resolution_queue_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "contradiction-resolution-queue-v0",
        "watch_queue_score": d("0.350000"),
        "block_queue_score": d("0.700000"),
        "stale_source_age_seconds": d("3600.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchCrossSourceContradictionResolutionQueueConfig(**values)


def item(
    item_id: str = "queue-alpha",
    *,
    source_class_pair: tuple[str, str] = ("official_reporting", "specialist_analysis"),
    observed_at: datetime = OBSERVED_AT,
    aggregate_contradiction_severity: Decimal = d("0.100000"),
    source_reliability_memory: Decimal = d("0.900000"),
    source_age_seconds: Decimal = d("300.000000"),
    rule_clarity: Decimal = d("0.950000"),
    deadline_pressure: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = ("contradiction_supplied",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchCrossSourceContradictionResolutionQueueInput(
        queue_item_id=item_id,
        source_class_pair=source_class_pair,
        observed_at=observed_at,
        aggregate_contradiction_severity=aggregate_contradiction_severity,
        source_reliability_memory=source_reliability_memory,
        source_age_seconds=source_age_seconds,
        rule_clarity=rule_clarity,
        deadline_pressure=deadline_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, generated_at: datetime = GENERATED_AT, config: object | None = None):
    module = api()
    return module.build_research_cross_source_contradiction_resolution_queue_report(
        items,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_code_counts"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "severity",
                "memory",
                "age",
                "freshness",
                "clarity",
                "pressure",
                "score",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


def test_empty_input_returns_pass_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == "contradiction-resolution-queue-v0"
    assert empty_report.status == "pass"
    assert empty_report.reason_codes == ("contradiction_resolution_queue_passed",)
    assert empty_report.item_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.max_queue_score == d("0.000000")
    assert empty_report.max_aggregate_contradiction_severity == d("0.000000")
    assert empty_report.max_deadline_pressure == d("0.000000")
    assert empty_report.max_source_age_seconds == d("0.000000")
    assert empty_report.reason_code_counts == ()
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_numbers(empty_report)

    payload = module.research_cross_source_contradiction_resolution_queue_payload(
        empty_report,
    )
    digest_value = module.research_cross_source_contradiction_resolution_queue_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert payload["status"] == "pass"
    assert payload["item_count"] == "0"
    assert len(digest_value) == 64
    assert module.research_cross_source_contradiction_resolution_queue_digest(
        empty_report,
    ) == digest_value


def test_queue_scores_combine_severity_memory_freshness_clarity_and_deadline() -> None:
    queued = report(
        item(),
        item(
            "queue-watch",
            source_class_pair=("specialist_analysis", "derived_model"),
            aggregate_contradiction_severity=d("0.550000"),
            source_reliability_memory=d("0.500000"),
            source_age_seconds=d("1800.000000"),
            rule_clarity=d("0.600000"),
            deadline_pressure=d("0.450000"),
        ),
        item(
            "queue-block",
            source_class_pair=("official_reporting", "derived_model"),
            aggregate_contradiction_severity=d("0.900000"),
            source_reliability_memory=d("0.200000"),
            source_age_seconds=d("5400.000000"),
            rule_clarity=d("0.250000"),
            deadline_pressure=d("0.800000"),
        ),
    )

    assert queued.status == "block"
    assert queued.pass_count == d("1")
    assert queued.watch_count == d("1")
    assert queued.block_count == d("1")
    assert tuple(row.queue_item_id for row in queued.rows) == (
        "queue-block",
        "queue-watch",
        "queue-alpha",
    )

    blocked, watched, passed = queued.rows
    assert blocked.queue_status == "block"
    assert blocked.freshness_risk == d("1.000000")
    assert blocked.rule_ambiguity == d("0.750000")
    assert blocked.reliability_gap == d("0.800000")
    assert blocked.queue_score == d("0.850000")
    assert blocked.reason_codes == (
        "aggregate_contradiction_severity_block",
        "contradiction_supplied",
        "deadline_pressure_block",
        "freshness_risk_block",
        "queue_score_block",
        "reliability_gap_block",
        "rule_ambiguity_block",
    )

    assert watched.queue_status == "watch"
    assert watched.freshness_risk == d("0.500000")
    assert watched.rule_ambiguity == d("0.400000")
    assert watched.reliability_gap == d("0.500000")
    assert watched.queue_score == d("0.480000")
    assert watched.reason_codes == (
        "aggregate_contradiction_severity_watch",
        "contradiction_supplied",
        "deadline_pressure_watch",
        "freshness_risk_watch",
        "queue_score_watch",
        "reliability_gap_watch",
        "rule_ambiguity_watch",
    )

    assert passed.queue_status == "pass"
    assert passed.freshness_risk == d("0.083333")
    assert passed.queue_score == d("0.076667")
    assert passed.reason_codes == (
        "contradiction_resolution_queue_passed",
        "contradiction_supplied",
    )

    assert queued.reason_codes == (
        "aggregate_contradiction_severity_block",
        "aggregate_contradiction_severity_watch",
        "deadline_pressure_block",
        "deadline_pressure_watch",
        "freshness_risk_block",
        "freshness_risk_watch",
        "queue_score_block",
        "queue_score_watch",
        "reliability_gap_block",
        "reliability_gap_watch",
        "rule_ambiguity_block",
        "rule_ambiguity_watch",
    )


def test_payload_and_digest_are_deterministic_and_public_safe() -> None:
    module = api()
    first = report(
        item("zeta", source_class_pair=("derived_model", "official_reporting")),
        item("alpha", source_class_pair=("official_reporting", "specialist_analysis")),
    )
    second = report(
        item("alpha", source_class_pair=("specialist_analysis", "official_reporting")),
        item("zeta", source_class_pair=("official_reporting", "derived_model")),
    )

    first_payload = module.research_cross_source_contradiction_resolution_queue_payload(first)
    second_payload = module.research_cross_source_contradiction_resolution_queue_payload(second)

    assert first_payload == second_payload
    assert module.research_cross_source_contradiction_resolution_queue_digest(
        first,
    ) == module.research_cross_source_contradiction_resolution_queue_digest(second)
    assert tuple(row.source_class_pair for row in first.rows) == (
        ("derived_model", "official_reporting"),
        ("official_reporting", "specialist_analysis"),
    )

    rendered = json.dumps(first_payload, sort_keys=True)
    for forbidden in (
        "https://",
        "postgres://",
        "secret-token",
        "question-",
        "market-",
        "slug",
        "http://",
    ):
        assert forbidden not in rendered.lower()

    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["rows"][0]["paper_only"] is True
    assert first_payload["rows"][0]["report_only"] is True
    assert first_payload["rows"][0]["readonly"] is True
    assert_no_public_number_payload(first_payload)


def test_reason_code_counts_are_deterministic_and_unique() -> None:
    module = api()
    queued = report(
        item(
            "zeta",
            aggregate_contradiction_severity=d("0.710000"),
            source_reliability_memory=d("0.650001"),
            source_age_seconds=d("1259.996400"),
            rule_clarity=d("0.650001"),
            deadline_pressure=d("0.349999"),
            reason_codes=("shared_reason",),
        ),
        item(
            "alpha",
            aggregate_contradiction_severity=d("0.710000"),
            source_reliability_memory=d("0.650001"),
            source_age_seconds=d("1259.996400"),
            rule_clarity=d("0.650001"),
            deadline_pressure=d("0.349999"),
            reason_codes=("alpha_reason", "shared_reason"),
        ),
    )

    assert all(len(row.reason_codes) == len(set(row.reason_codes)) for row in queued.rows)
    assert queued.reason_code_counts == (
        module.ResearchCrossSourceContradictionResolutionQueueReasonCodeCount(
            reason_code="aggregate_contradiction_severity_block",
            count=d("2"),
        ),
        module.ResearchCrossSourceContradictionResolutionQueueReasonCodeCount(
            reason_code="queue_score_watch",
            count=d("2"),
        ),
        module.ResearchCrossSourceContradictionResolutionQueueReasonCodeCount(
            reason_code="shared_reason",
            count=d("2"),
        ),
        module.ResearchCrossSourceContradictionResolutionQueueReasonCodeCount(
            reason_code="alpha_reason",
            count=d("1"),
        ),
    )


def test_utc_aware_datetimes_only_and_offsets_normalize_to_utc() -> None:
    offset_time = datetime(
        2026,
        7,
        8,
        7,
        30,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    queued = report(
        item(observed_at=offset_time),
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert queued.generated_at == GENERATED_AT
    assert queued.rows[0].observed_at == OBSERVED_AT

    with pytest.raises(ValueError, match="observed_at"):
        item(observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(item(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        item(observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="generated_at"):
        report(item(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))


def test_public_dataclasses_are_frozen_decimal_only_and_validate_flags() -> None:
    module = api()

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    queued = report(item())
    row = queued.rows[0]
    reason_count = queued.reason_code_counts[0]

    with pytest.raises(FrozenInstanceError):
        queued.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.queue_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(item(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(queued, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(reason_count, paper_only=False)

    for value in (cfg(), item(), row, reason_count, queued):
        assert_decimal_public_numbers(value)

    with pytest.raises(ValueError, match="aggregate_contradiction_severity"):
        item(aggregate_contradiction_severity=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability_memory"):
        item(source_reliability_memory=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="deadline_pressure"):
        item(deadline_pressure=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="watch_queue_score"):
        cfg(watch_queue_score=1)  # type: ignore[arg-type]


def test_validation_rejects_bad_inputs_and_inconsistent_manual_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_class_pair"):
        item(source_class_pair=("official_reporting", "official_reporting"))
    with pytest.raises(ValueError, match="source_class_pair"):
        item(source_class_pair=("official_reporting", "https://source.example.test"))
    with pytest.raises(ValueError, match="queue_item_id"):
        item(item_id="")
    with pytest.raises(ValueError, match="watch_queue_score"):
        cfg(watch_queue_score=d("0.710000"))
    with pytest.raises(ValueError, match="reason_codes"):
        item(reason_codes=("same_reason", "same_reason"))
    with pytest.raises(ValueError, match="queue_items"):
        module.build_research_cross_source_contradiction_resolution_queue_report(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate queue_item_id"):
        report(item(), item(source_class_pair=("official_reporting", "derived_model")))
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_cross_source_contradiction_resolution_queue_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report must be"):
        module.research_cross_source_contradiction_resolution_queue_payload(object())
    with pytest.raises(ValueError, match="report must be"):
        module.research_cross_source_contradiction_resolution_queue_digest(object())

    queued = report(item())
    with pytest.raises(ValueError, match="item_count"):
        replace(queued, item_count=d("2"))
    with pytest.raises(ValueError, match="rows"):
        replace(queued, rows=())
    with pytest.raises(ValueError, match="max_queue_score"):
        replace(queued, max_queue_score=d("0.500000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(queued, reason_code_counts=())


def test_module_source_is_pure_public_report_only_without_runtime_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "private_key",
        "api_key",
        "recommend",
        "sizing",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "websocket",
        "sqlite",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "pathlib",
        "url",
        "raw_source",
        "source_text",
        "source_name",
        "source_ref",
        "market",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
