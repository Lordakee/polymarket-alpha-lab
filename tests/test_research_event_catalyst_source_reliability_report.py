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


GENERATED_AT = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab.research_event_catalyst_source_reliability_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_catalyst_source_reliability_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "max_pass_catalyst_recency_hours": d("24.000000"),
        "max_watch_catalyst_recency_hours": d("72.000000"),
        "min_pass_source_reliability_score": d("0.800000"),
        "min_watch_source_reliability_score": d("0.600000"),
        "max_pass_contradiction_count": d("0"),
        "max_watch_contradiction_count": d("2"),
        "max_pass_coverage_gap_ratio": d("0.100000"),
        "max_watch_coverage_gap_ratio": d("0.300000"),
        "max_pass_team_capacity_utilization_ratio": d("0.800000"),
        "max_watch_team_capacity_utilization_ratio": d("1.000000"),
    }
    values.update(overrides)
    return module.ResearchEventCatalystSourceReliabilityConfig(**values)


def source_class(
    event_domain: str,
    source_class: str,
    *,
    catalyst_observation_count: Decimal = d("4"),
    average_catalyst_recency_hours: Decimal = d("12.000000"),
    source_reliability_score: Decimal = d("0.900000"),
    contradiction_count: Decimal = d("0"),
    coverage_gap_ratio: Decimal = d("0.050000"),
    team_capacity_utilization_ratio: Decimal = d("0.500000"),
):
    module = api()
    return module.ResearchEventCatalystSourceReliabilityInput(
        event_domain=event_domain,
        source_class=source_class,
        catalyst_observation_count=catalyst_observation_count,
        average_catalyst_recency_hours=average_catalyst_recency_hours,
        source_reliability_score=source_reliability_score,
        contradiction_count=contradiction_count,
        coverage_gap_ratio=coverage_gap_ratio,
        team_capacity_utilization_ratio=team_capacity_utilization_ratio,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_event_catalyst_source_reliability_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_summarizes_catalyst_source_reliability_by_event_domain() -> None:
    module = api()

    reliability_report = report(
        source_class(
            "macro-policy",
            "official-calendar",
            catalyst_observation_count=d("5"),
            average_catalyst_recency_hours=d("8.000000"),
            source_reliability_score=d("0.920000"),
            contradiction_count=d("0"),
            coverage_gap_ratio=d("0.050000"),
            team_capacity_utilization_ratio=d("0.500000"),
        ),
        source_class(
            "macro-policy",
            "expert-transcript",
            catalyst_observation_count=d("3"),
            average_catalyst_recency_hours=d("48.000000"),
            source_reliability_score=d("0.700000"),
            contradiction_count=d("1"),
            coverage_gap_ratio=d("0.200000"),
            team_capacity_utilization_ratio=d("0.950000"),
        ),
        source_class(
            "weather-risk",
            "local-agency-bulletin",
            catalyst_observation_count=d("1"),
            average_catalyst_recency_hours=d("96.000000"),
            source_reliability_score=d("0.450000"),
            contradiction_count=d("4"),
            coverage_gap_ratio=d("0.500000"),
            team_capacity_utilization_ratio=d("1.000000"),
        ),
    )

    assert type(reliability_report) is module.ResearchEventCatalystSourceReliabilityReport
    assert reliability_report.status == "block"
    assert reliability_report.input_count == d("3")
    assert reliability_report.event_domain_count == d("2")
    assert reliability_report.source_class_count == d("3")
    assert reliability_report.pass_count == d("1")
    assert reliability_report.watch_count == d("1")
    assert reliability_report.block_count == d("1")
    assert reliability_report.stale_catalyst_count == d("2")
    assert reliability_report.low_reliability_count == d("2")
    assert reliability_report.contradiction_count == d("5")
    assert reliability_report.coverage_gap_count == d("2")
    assert reliability_report.capacity_pressure_count == d("2")
    assert reliability_report.average_catalyst_recency_hours == d("50.666667")
    assert reliability_report.average_source_reliability_score == d("0.690000")
    assert reliability_report.max_coverage_gap_ratio == d("0.500000")
    assert reliability_report.max_team_capacity_utilization_ratio == d("1.000000")
    assert reliability_report.reason_codes == (
        "catalyst_recency_block",
        "source_reliability_block",
        "source_contradiction_block",
        "coverage_gap_block",
        "catalyst_recency_watch",
        "source_reliability_watch",
        "source_contradiction_watch",
        "coverage_gap_watch",
        "team_capacity_watch",
        "event_catalyst_source_reliability_report_block",
    )

    assert tuple(row.event_domain for row in reliability_report.rows) == (
        "weather-risk",
        "macro-policy",
        "macro-policy",
    )
    block_row, watch_row, pass_row = reliability_report.rows
    assert block_row.status == "block"
    assert block_row.reliability_risk_score == d("1.000000")
    assert block_row.reason_codes == (
        "catalyst_recency_block",
        "source_reliability_block",
        "source_contradiction_block",
        "coverage_gap_block",
        "team_capacity_watch",
    )
    assert watch_row.status == "watch"
    assert watch_row.reliability_risk_score == d("0.500000")
    assert watch_row.reason_codes == (
        "catalyst_recency_watch",
        "source_reliability_watch",
        "source_contradiction_watch",
        "coverage_gap_watch",
        "team_capacity_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ()

    payload = module.research_event_catalyst_source_reliability_report_payload(
        reliability_report,
    )
    assert payload["generated_at"] == "2026-07-08T15:00:00+00:00"
    assert payload["status"] == "block"
    assert payload["input_count"] == "3"
    assert payload["average_source_reliability_score"] == "0.690000"
    assert payload["rows"][0]["source_class"] == "local-agency-bulletin"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == (
        reliability_report.derived_validation_digest
    )
    assert len(payload["derived_validation_digest"]) == 64
    assert module.validate_research_event_catalyst_source_reliability_public_payload(
        payload,
    )
    assert_no_numeric_payload(payload)
    assert_no_forbidden_payload_language(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_payload_and_digest_are_deterministic_across_input_sequence() -> None:
    module = api()
    inputs = (
        source_class("zeta-domain", "calendar-feed"),
        source_class(
            "alpha-domain",
            "audit-summary",
            average_catalyst_recency_hours=d("80.000000"),
            source_reliability_score=d("0.550000"),
            contradiction_count=d("3"),
            coverage_gap_ratio=d("0.400000"),
            team_capacity_utilization_ratio=d("1.000000"),
        ),
        source_class(
            "middle-domain",
            "specialist-notes",
            average_catalyst_recency_hours=d("36.000000"),
            source_reliability_score=d("0.700000"),
            contradiction_count=d("1"),
            coverage_gap_ratio=d("0.200000"),
            team_capacity_utilization_ratio=d("0.900000"),
        ),
    )

    first = report(*inputs)
    second = report(*reversed(inputs))

    assert tuple(row.event_domain for row in first.rows) == (
        "alpha-domain",
        "middle-domain",
        "zeta-domain",
    )
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_event_catalyst_source_reliability_report_payload(
        first,
    ) == module.research_event_catalyst_source_reliability_report_payload(second)


def test_timezone_normalization_empty_input_and_public_payload_validation() -> None:
    module = api()

    eastern = timezone(timedelta(hours=-4))
    timezone_report = report(
        source_class("timezone-domain", "public-calendar"),
        generated_at=datetime(2026, 7, 8, 11, 0, tzinfo=eastern),
    )
    assert timezone_report.generated_at == GENERATED_AT
    assert (
        module.research_event_catalyst_source_reliability_report_payload(
            timezone_report,
        )["generated_at"]
        == "2026-07-08T15:00:00+00:00"
    )

    empty_report = report()
    assert empty_report.status == "block"
    assert empty_report.input_count == d("0")
    assert empty_report.event_domain_count == d("0")
    assert empty_report.average_catalyst_recency_hours is None
    assert empty_report.average_source_reliability_score is None
    assert empty_report.max_coverage_gap_ratio is None
    assert empty_report.reason_codes == (
        "event_catalyst_source_reliability_report_no_inputs",
    )
    assert module.validate_research_event_catalyst_source_reliability_public_payload(
        module.research_event_catalyst_source_reliability_report_payload(empty_report),
    )


def test_dataclasses_are_frozen_decimal_only_flagged_and_digest_bound() -> None:
    module = api()

    for klass in (
        module.ResearchEventCatalystSourceReliabilityConfig,
        module.ResearchEventCatalystSourceReliabilityInput,
        module.ResearchEventCatalystSourceReliabilityReasonCodeCount,
        module.ResearchEventCatalystSourceReliabilityRow,
        module.ResearchEventCatalystSourceReliabilityReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="max_pass_catalyst_recency_hours"):
        config(max_pass_catalyst_recency_hours=24)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability_score"):
        source_class("bad-decimal-domain", "calendar", source_reliability_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="coverage_gap_ratio"):
        source_class(
            "bad-decimal-domain",
            "calendar",
            coverage_gap_ratio=_DecimalSubclass("0.100000"),
        )

    input_row = source_class("frozen-domain", "calendar")
    with pytest.raises(FrozenInstanceError):
        input_row.event_domain = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    good_report = report(input_row)
    with pytest.raises(FrozenInstanceError):
        good_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(good_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="input_count"):
        replace(good_report, input_count=1)  # type: ignore[arg-type]

    for item in (
        input_row,
        good_report.rows[0],
        good_report.reason_code_counts[0] if good_report.reason_code_counts else None,
        good_report,
    ):
        if item is None:
            continue
        for field in fields(item):
            value = getattr(item, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal

    tampered = replace(good_report)
    object.__setattr__(tampered, "source_class_count", d("99"))
    with pytest.raises(ValueError, match="source_class_count|derived_validation_digest"):
        module.research_event_catalyst_source_reliability_report_payload(tampered)


def test_validates_inputs_thresholds_public_payload_and_unsafe_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="max_pass_catalyst_recency_hours"):
        config(max_pass_catalyst_recency_hours=d("80.000000"))
    with pytest.raises(ValueError, match="min_pass_source_reliability_score"):
        config(min_pass_source_reliability_score=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_contradiction_count"):
        config(max_pass_contradiction_count=d("3"))
    with pytest.raises(ValueError, match="max_pass_coverage_gap_ratio"):
        config(max_pass_coverage_gap_ratio=d("0.400000"))
    with pytest.raises(ValueError, match="catalyst_observation_count"):
        source_class(
            "bad-count-domain",
            "calendar",
            catalyst_observation_count=d("0"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            source_class("bad-generated-domain", "calendar"),
            generated_at=datetime(2026, 7, 8, 15, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            source_class("bad-offset-domain", "calendar"),
            generated_at=datetime(2026, 7, 8, 15, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_event_catalyst_source_reliability_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(
            source_class("duplicate-domain", "calendar"),
            source_class("duplicate-domain", "calendar"),
        )
    with pytest.raises(ValueError, match="unsupported"):
        config(config_version="research-event-catalyst-source-reliability-v1")

    payload = module.research_event_catalyst_source_reliability_report_payload(
        report(source_class("payload-domain", "calendar")),
    )
    assert module.validate_research_event_catalyst_source_reliability_public_payload(
        payload,
    )
    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_research_event_catalyst_source_reliability_public_payload(
            {**payload, "input_count": 1},
        )
    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_catalyst_source_reliability_public_payload(
            missing_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_catalyst_source_reliability_public_payload(
            {**payload, "source_class_count": "9"},
        )

    for forbidden_key in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_identifier",
        "wallet_address",
        "auth_token",
        "order_id",
        "trade_intent",
        "live_execution",
        "stake_size",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe|raw identifier|action language"):
            module.validate_research_event_catalyst_source_reliability_public_payload(
                {**payload, forbidden_key: "not allowed"},
            )


def test_module_scope_is_report_only_readonly_and_external_io_free() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source_text.lower()
    for forbidden in (
        "wallet",
        "auth",
        "account",
        "broker",
        "database",
        "payload_json",
        "open(",
        "requests",
        "http",
        "network",
        "submit",
        "place",
        "persist",
        "recommend",
        "sizing",
        "position_size",
        "stake",
        "allocation",
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "raw_event",
        "raw_market",
        "raw_source",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    forbidden_import_fragments = (
        "db",
        "env",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_numeric_payload(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | float | Decimal):
        raise AssertionError(f"numeric payload value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_numeric_payload(item)


def assert_no_forbidden_payload_language(payload: dict[str, Any]) -> None:
    payload_text = repr(payload).lower()
    for forbidden in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_identifier",
        "wallet",
        "auth",
        "order",
        "trade",
        "live_execution",
        "recommend",
        "sizing",
        "position_size",
        "stake",
    ):
        assert forbidden not in payload_text
