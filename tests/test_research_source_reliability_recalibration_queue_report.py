from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_source_reliability_recalibration_queue_report import (
    DEFAULT_RESEARCH_SOURCE_RELIABILITY_RECALIBRATION_QUEUE_REPORT_CONFIG_VERSION,
    RECALIBRATION_QUEUE_STATUSES,
    ResearchSourceReliabilityRecalibrationQueueConfig,
    ResearchSourceReliabilityRecalibrationQueueInput,
    ResearchSourceReliabilityRecalibrationQueueReasonCodeCount,
    ResearchSourceReliabilityRecalibrationQueueReport,
    ResearchSourceReliabilityRecalibrationQueueRow,
    build_research_source_reliability_recalibration_queue_report,
    research_source_reliability_recalibration_queue_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=30)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchSourceReliabilityRecalibrationQueueConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_SOURCE_RELIABILITY_RECALIBRATION_QUEUE_REPORT_CONFIG_VERSION
        ),
        "max_pass_aggregate_source_age_seconds": d("86400.000000"),
        "max_watch_aggregate_source_age_seconds": d("604800.000000"),
        "min_pass_historical_reliability_score": d("0.800000"),
        "min_watch_historical_reliability_score": d("0.600000"),
        "max_pass_contradiction_pressure": d("0.100000"),
        "max_watch_contradiction_pressure": d("0.300000"),
        "max_pass_evidence_miss_rate": d("0.050000"),
        "max_watch_evidence_miss_rate": d("0.200000"),
        "min_pass_team_capacity_ratio": d("0.600000"),
        "min_watch_team_capacity_ratio": d("0.300000"),
    }
    values.update(overrides)
    return ResearchSourceReliabilityRecalibrationQueueConfig(**values)


def input_row(
    domain: str = "politics",
    source_family: str = "official",
    *,
    aggregate_source_age_seconds: Decimal = d("3600.000000"),
    historical_reliability_score: Decimal = d("0.920000"),
    contradiction_pressure: Decimal = d("0.030000"),
    evidence_miss_rate: Decimal = d("0.010000"),
    team_capacity_ratio: Decimal = d("0.800000"),
    observation_count: Decimal = d("12.000000"),
    observed_at: datetime = OBSERVED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceReliabilityRecalibrationQueueInput:
    return ResearchSourceReliabilityRecalibrationQueueInput(
        domain=domain,
        source_family=source_family,
        aggregate_source_age_seconds=aggregate_source_age_seconds,
        historical_reliability_score=historical_reliability_score,
        contradiction_pressure=contradiction_pressure,
        evidence_miss_rate=evidence_miss_rate,
        team_capacity_ratio=team_capacity_ratio,
        observation_count=observation_count,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchSourceReliabilityRecalibrationQueueInput,
    cfg: ResearchSourceReliabilityRecalibrationQueueConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceReliabilityRecalibrationQueueReport:
    return build_research_source_reliability_recalibration_queue_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_recalibration_queue_scores_pass_watch_and_block_statuses() -> None:
    digest = report(
        input_row(
            "politics",
            "official",
            aggregate_source_age_seconds=d("3600.000000"),
            historical_reliability_score=d("0.920000"),
            contradiction_pressure=d("0.030000"),
            evidence_miss_rate=d("0.010000"),
            team_capacity_ratio=d("0.800000"),
        ),
        input_row(
            "crypto",
            "proxy",
            aggregate_source_age_seconds=d("172800.000000"),
            historical_reliability_score=d("0.700000"),
            contradiction_pressure=d("0.200000"),
            evidence_miss_rate=d("0.100000"),
            team_capacity_ratio=d("0.500000"),
        ),
        input_row(
            "equities",
            "community",
            aggregate_source_age_seconds=d("900000.000000"),
            historical_reliability_score=d("0.400000"),
            contradiction_pressure=d("0.500000"),
            evidence_miss_rate=d("0.350000"),
            team_capacity_ratio=d("0.100000"),
        ),
    )

    assert is_dataclass(digest)
    assert RECALIBRATION_QUEUE_STATUSES == ("pass", "watch", "block")
    assert digest.generated_at == GENERATED_AT
    assert (
        digest.config_version
        == "research-source-reliability-recalibration-queue-report-v1"
    )
    assert digest.input_count == d("3.000000")
    assert digest.recalibration_task_count == d("2.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert digest.task_ratio == d("0.666667")
    assert digest.max_aggregate_source_age_seconds == d("900000.000000")
    assert digest.min_historical_reliability_score == d("0.400000")
    assert digest.max_contradiction_pressure == d("0.500000")
    assert digest.max_evidence_miss_rate == d("0.350000")
    assert digest.min_team_capacity_ratio == d("0.100000")
    assert digest.status == "block"
    assert digest.queue_mode == "paper_recalibration_block"
    assert digest.reason_codes == (
        "recalibration_queue_block",
        "aggregate_source_age_block",
        "historical_reliability_low_block",
        "contradiction_pressure_high_block",
        "evidence_miss_rate_high_block",
        "team_capacity_low_block",
        "aggregate_source_age_watch",
        "historical_reliability_thin_watch",
        "contradiction_pressure_elevated_watch",
        "evidence_miss_rate_elevated_watch",
        "team_capacity_thin_watch",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert len(digest.derived_validation_digest) == 64

    blocked, watched, passed = digest.rows
    assert tuple(row.queue_status for row in digest.rows) == ("block", "watch", "pass")
    assert blocked.domain == "equities"
    assert blocked.source_family == "community"
    assert blocked.reason_codes == (
        "aggregate_source_age_block",
        "historical_reliability_low_block",
        "contradiction_pressure_high_block",
        "evidence_miss_rate_high_block",
        "team_capacity_low_block",
    )
    assert watched.reason_codes == (
        "aggregate_source_age_watch",
        "historical_reliability_thin_watch",
        "contradiction_pressure_elevated_watch",
        "evidence_miss_rate_elevated_watch",
        "team_capacity_thin_watch",
    )
    assert passed.reason_codes == ("recalibration_queue_clear",)
    assert ResearchSourceReliabilityRecalibrationQueueReasonCodeCount(
        reason_code="aggregate_source_age_block",
        count=d("1.000000"),
        row_ratio=d("0.333333"),
    ) in digest.reason_code_counts


def test_empty_queue_is_pass_with_decimal_counts_and_hard_flags() -> None:
    digest = report()

    assert digest.input_count == ZERO
    assert digest.recalibration_task_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.block_count == ZERO
    assert digest.task_ratio == ZERO
    assert digest.max_aggregate_source_age_seconds == ZERO
    assert digest.min_historical_reliability_score == ZERO
    assert digest.max_contradiction_pressure == ZERO
    assert digest.max_evidence_miss_rate == ZERO
    assert digest.min_team_capacity_ratio == ZERO
    assert digest.status == "pass"
    assert digest.queue_mode == "paper_monitor_only"
    assert digest.reason_codes == ("recalibration_queue_empty",)
    assert digest.reason_code_counts == ()
    assert digest.rows == ()

    populated = report(input_row())
    for value in (digest, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_score", "_ratio", "_seconds", "_rate")):
                assert type(item_value) is Decimal


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    first = report(
        input_row(
            "sports",
            "proxy",
            aggregate_source_age_seconds=d("120000.000000"),
            historical_reliability_score=d("0.700000"),
            contradiction_pressure=d("0.120000"),
            evidence_miss_rate=d("0.060000"),
            team_capacity_ratio=d("0.500000"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        input_row("politics", "official"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = report(
        input_row("politics", "official"),
        input_row(
            "sports",
            "proxy",
            aggregate_source_age_seconds=d("120000.000000"),
            historical_reliability_score=d("0.700000"),
            contradiction_pressure=d("0.120000"),
            evidence_miss_rate=d("0.060000"),
            team_capacity_ratio=d("0.500000"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = research_source_reliability_recalibration_queue_report_payload(first)
    repeat_payload = research_source_reliability_recalibration_queue_report_payload(
        second,
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["rows"][0]["aggregate_source_age_seconds"] == "120000.000000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_public_numeric_values(payload)
    json.dumps(payload, sort_keys=True)

    raw_source_fragments = (
        "source_name",
        "source_url",
        "source_text",
        "source_ref",
        "source_reference",
        "raw_source",
        "raw_text",
        "url",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in raw_source_fragments
    )
    assert "blocked" not in json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_reliability_recalibration_queue_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2.000000"))


def test_public_payload_rejects_raw_identifiers_unsafe_flags_and_numbers() -> None:
    payload = research_source_reliability_recalibration_queue_report_payload(
        report(input_row()),
    )

    for key in (
        "source_name",
        "source_url",
        "source_text",
        "source_ref",
        "raw_source_text",
        "wallet_route",
        "auth_header",
        "order_route",
        "trade_mode",
        "live_execution",
        "db_write_path",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            research_source_reliability_recalibration_queue_report_payload(unsafe)

    numeric = dict(payload)
    numeric["input_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        research_source_reliability_recalibration_queue_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_source_reliability_recalibration_queue_report_payload(downgraded)


def test_validation_rejects_non_decimals_duplicates_bad_labels_and_time_boundaries() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        input_row(aggregate_source_age_seconds=60)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        input_row(historical_reliability_score=_DecimalSubclass("0.600000"))

    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 12, 0))

    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 30, tzinfo=UTC))

    with pytest.raises(ValueError, match="future"):
        report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unique"):
        report(input_row(), input_row())

    with pytest.raises(ValueError, match="domain"):
        input_row("weather", "official")

    with pytest.raises(ValueError, match="source_family"):
        input_row("politics", "raw-name")

    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)

    with pytest.raises(ValueError, match="subclass"):
        type(
            "ConfigSubclass",
            (ResearchSourceReliabilityRecalibrationQueueConfig,),
            {},
        )

    frozen = input_row()
    with pytest.raises(FrozenInstanceError):
        frozen.domain = "crypto"  # type: ignore[misc]


def test_materialized_row_and_report_fields_are_revalidated() -> None:
    digest = report(input_row())
    row = digest.rows[0]

    with pytest.raises(ValueError, match="queue_status"):
        ResearchSourceReliabilityRecalibrationQueueRow(
            **{
                **row.__dict__,
                "queue_status": "block",
            },
        )

    with pytest.raises(ValueError, match="status"):
        ResearchSourceReliabilityRecalibrationQueueReport(
            **{
                **digest.__dict__,
                "status": "block",
                "queue_mode": "paper_recalibration_block",
                "derived_validation_digest": "",
            },
        )


def test_module_exposes_no_db_network_wallet_auth_order_trade_live_or_write_surface() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_reliability_recalibration_queue_report.py"
    )
    tree = ast.parse(module_path.read_text())
    module_text = module_path.read_text().lower()
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }

    assert "recommendation" not in module_text
    assert "sizing" not in module_text

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
