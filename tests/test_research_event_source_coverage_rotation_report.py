from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_source_coverage_rotation_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTzinfo(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_EVENT_SOURCE_COVERAGE_ROTATION_REPORT_CONFIG_VERSION
        ),
        "fresh_source_max_age_seconds": d("7200.000000"),
        "minimum_source_class_count": d("2.000000"),
        "minimum_aggregate_source_count": d("3.000000"),
        "minimum_reliability_memory_score": d("0.650000"),
        "watch_catalyst_pressure_score": d("0.600000"),
        "block_catalyst_pressure_score": d("0.850000"),
        "minimum_team_capacity_available": d("1.000000"),
        "max_team_capacity_load_ratio": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchEventSourceCoverageRotationConfig(**values)


def signal(
    event_domain: str = "macro_release",
    source_class: str = "official_aggregate",
    *,
    observed_at: datetime | None = None,
    aggregate_source_count: Decimal = d("3.000000"),
    reliability_memory_score: Decimal = d("0.900000"),
    catalyst_pressure_score: Decimal = d("0.300000"),
    team_capacity_available: Decimal = d("4.000000"),
    team_capacity_load_ratio: Decimal = d("0.500000"),
) -> Any:
    module = api()
    return module.ResearchEventSourceCoverageRotationSignal(
        event_domain=event_domain,
        source_class=source_class,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        aggregate_source_count=aggregate_source_count,
        reliability_memory_score=reliability_memory_score,
        catalyst_pressure_score=catalyst_pressure_score,
        team_capacity_available=team_capacity_available,
        team_capacity_load_ratio=team_capacity_load_ratio,
    )


def report(
    *signals: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_event_source_coverage_rotation_report(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def mixed_report() -> Any:
    return report(
        signal(
            "weather_event",
            "official_aggregate",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            aggregate_source_count=d("2.000000"),
            reliability_memory_score=d("0.700000"),
            catalyst_pressure_score=d("0.650000"),
            team_capacity_available=d("2.000000"),
            team_capacity_load_ratio=d("0.700000"),
        ),
        signal(
            "macro_release",
            "official_aggregate",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            aggregate_source_count=d("3.000000"),
            reliability_memory_score=d("0.900000"),
            catalyst_pressure_score=d("0.300000"),
            team_capacity_available=d("4.000000"),
            team_capacity_load_ratio=d("0.500000"),
        ),
        signal(
            "policy_window",
            "official_aggregate",
            observed_at=GENERATED_AT - timedelta(hours=3),
            aggregate_source_count=d("1.000000"),
            reliability_memory_score=d("0.400000"),
            catalyst_pressure_score=d("0.920000"),
            team_capacity_available=ZERO,
            team_capacity_load_ratio=d("0.950000"),
        ),
        signal(
            "macro_release",
            "independent_aggregate",
            observed_at=GENERATED_AT - timedelta(minutes=35),
            aggregate_source_count=d("4.000000"),
            reliability_memory_score=d("0.800000"),
            catalyst_pressure_score=d("0.400000"),
            team_capacity_available=d("3.000000"),
            team_capacity_load_ratio=d("0.600000"),
        ),
        signal(
            "weather_event",
            "specialist_aggregate",
            observed_at=GENERATED_AT - timedelta(hours=2, minutes=30),
            aggregate_source_count=d("2.000000"),
            reliability_memory_score=d("0.650000"),
            catalyst_pressure_score=d("0.700000"),
            team_capacity_available=d("2.000000"),
            team_capacity_load_ratio=d("0.800000"),
        ),
    )


def test_rotation_report_reduces_domains_and_sorts_deterministically() -> None:
    module = api()
    result = mixed_report()

    assert isinstance(result, module.ResearchEventSourceCoverageRotationReport)
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == (
        module.DEFAULT_RESEARCH_EVENT_SOURCE_COVERAGE_ROTATION_REPORT_CONFIG_VERSION
    )
    assert module.STATUSES == ("pass", "watch", "block")
    assert result.report_status == "block"
    assert result.next_step == (
        "block_report_only_research_event_source_coverage_rotation_report"
    )
    assert result.domain_count == d("3.000000")
    assert result.pass_domain_count == d("1.000000")
    assert result.watch_domain_count == d("1.000000")
    assert result.block_domain_count == d("1.000000")
    assert result.thin_coverage_domain_count == d("1.000000")
    assert result.stale_source_domain_count == d("2.000000")
    assert result.weak_reliability_domain_count == d("1.000000")
    assert result.high_catalyst_domain_count == d("1.000000")
    assert result.capacity_constrained_domain_count == d("1.000000")
    assert result.max_source_age_seconds == d("10800.000000")
    assert result.average_reliability_memory_score == d("0.641667")
    assert result.max_catalyst_pressure_score == d("0.920000")
    assert tuple(row.event_domain for row in result.rows) == (
        "policy_window",
        "weather_event",
        "macro_release",
    )

    blocked = result.rows[0]
    assert blocked.rotation_status == "block"
    assert blocked.source_class_count == d("1.000000")
    assert blocked.aggregate_source_count == d("1.000000")
    assert blocked.max_source_age_seconds == d("10800.000000")
    assert blocked.average_reliability_memory_score == d("0.400000")
    assert blocked.max_catalyst_pressure_score == d("0.920000")
    assert blocked.min_team_capacity_available == ZERO
    assert blocked.max_team_capacity_load_ratio == d("0.950000")
    assert blocked.reason_codes == (
        "research_event_source_coverage_rotation_report_thin_coverage",
        "research_event_source_coverage_rotation_report_stale_source_age",
        "research_event_source_coverage_rotation_report_weak_reliability_memory",
        "research_event_source_coverage_rotation_report_high_catalyst_pressure",
        "research_event_source_coverage_rotation_report_capacity_constrained",
    )
    assert result.reason_codes == (
        "research_event_source_coverage_rotation_report_thin_coverage",
        "research_event_source_coverage_rotation_report_stale_source_age",
        "research_event_source_coverage_rotation_report_weak_reliability_memory",
        "research_event_source_coverage_rotation_report_high_catalyst_pressure",
        "research_event_source_coverage_rotation_report_capacity_constrained",
        "research_event_source_coverage_rotation_report_pass",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in result.rows)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert result == report(*reversed((
        signal(
            "weather_event",
            "official_aggregate",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            aggregate_source_count=d("2.000000"),
            reliability_memory_score=d("0.700000"),
            catalyst_pressure_score=d("0.650000"),
            team_capacity_available=d("2.000000"),
            team_capacity_load_ratio=d("0.700000"),
        ),
        signal(
            "macro_release",
            "official_aggregate",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            aggregate_source_count=d("3.000000"),
            reliability_memory_score=d("0.900000"),
            catalyst_pressure_score=d("0.300000"),
            team_capacity_available=d("4.000000"),
            team_capacity_load_ratio=d("0.500000"),
        ),
        signal(
            "policy_window",
            "official_aggregate",
            observed_at=GENERATED_AT - timedelta(hours=3),
            aggregate_source_count=d("1.000000"),
            reliability_memory_score=d("0.400000"),
            catalyst_pressure_score=d("0.920000"),
            team_capacity_available=ZERO,
            team_capacity_load_ratio=d("0.950000"),
        ),
        signal(
            "macro_release",
            "independent_aggregate",
            observed_at=GENERATED_AT - timedelta(minutes=35),
            aggregate_source_count=d("4.000000"),
            reliability_memory_score=d("0.800000"),
            catalyst_pressure_score=d("0.400000"),
            team_capacity_available=d("3.000000"),
            team_capacity_load_ratio=d("0.600000"),
        ),
        signal(
            "weather_event",
            "specialist_aggregate",
            observed_at=GENERATED_AT - timedelta(hours=2, minutes=30),
            aggregate_source_count=d("2.000000"),
            reliability_memory_score=d("0.650000"),
            catalyst_pressure_score=d("0.700000"),
            team_capacity_available=d("2.000000"),
            team_capacity_load_ratio=d("0.800000"),
        ),
    )))


def test_empty_report_payload_and_digest_are_deterministic_decimal_strings() -> None:
    module = api()
    empty = report()

    assert empty.report_status == "block"
    assert empty.next_step == (
        "block_report_only_research_event_source_coverage_rotation_report"
    )
    assert empty.domain_count == ZERO
    assert empty.rows == ()
    assert empty.reason_codes == (
        "research_event_source_coverage_rotation_report_no_inputs",
    )
    assert empty.reason_code_counts == (
        module.ResearchEventSourceCoverageRotationReasonCodeCount(
            reason_code="research_event_source_coverage_rotation_report_no_inputs",
            count=d("1.000000"),
            domain_ratio=ZERO,
        ),
    )

    populated = mixed_report()
    payload = module.research_event_source_coverage_rotation_report_payload(populated)
    digest = module.research_event_source_coverage_rotation_report_digest(populated)

    assert json.dumps(payload, sort_keys=True)
    assert payload == module.research_event_source_coverage_rotation_report_payload(
        mixed_report(),
    )
    assert digest == module.research_event_source_coverage_rotation_report_digest(
        mixed_report(),
    )
    assert len(digest) == 64
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["domain_count"] == "3.000000"
    assert payload["rows"][0]["max_source_age_seconds"] == "10800.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))

    public = repr(payload).lower()
    for token in (
        "event_id",
        "market_slug",
        "condition_id",
        "source_id",
        "https://",
        "token=",
    ):
        assert token not in public

    with pytest.raises(ValueError, match="count must be positive"):
        module.ResearchEventSourceCoverageRotationReasonCodeCount(
            reason_code="research_event_source_coverage_rotation_report_no_inputs",
            count=ZERO,
            domain_ratio=ZERO,
        )

    for raw_payload in (payload, [payload], {"payload"}):
        with pytest.raises(
            ValueError,
            match="ResearchEventSourceCoverageRotationReport",
        ):
            module.research_event_source_coverage_rotation_report_payload(raw_payload)


def test_payload_revalidates_tampered_report_and_nested_fields() -> None:
    module = api()
    result = mixed_report()

    tampered_report = result
    object.__setattr__(tampered_report, "domain_count", d("99.000000"))
    with pytest.raises(ValueError, match="domain_count"):
        module.research_event_source_coverage_rotation_report_payload(tampered_report)

    nested_tampered_report = mixed_report()
    object.__setattr__(
        nested_tampered_report,
        "rows",
        (asdict(nested_tampered_report.rows[0]),),
    )
    with pytest.raises(ValueError, match="rows must contain"):
        module.research_event_source_coverage_rotation_report_payload(
            nested_tampered_report,
        )

    zero_count_report = mixed_report()
    object.__setattr__(
        zero_count_report.reason_code_counts[0],
        "count",
        ZERO,
    )
    with pytest.raises(ValueError, match="count"):
        module.research_event_source_coverage_rotation_report_payload(
            zero_count_report,
        )

    false_flag_report = mixed_report()
    object.__setattr__(false_flag_report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.research_event_source_coverage_rotation_report_payload(
            false_flag_report,
        )


def test_dataclasses_are_frozen_hard_flagged_and_decimal_only() -> None:
    module = api()
    cfg = config()
    source = signal()
    result = report(source, cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        source.aggregate_source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].source_class_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.domain_count = d("2.000000")  # type: ignore[misc]

    for public_type in (
        module.ResearchEventSourceCoverageRotationConfig,
        module.ResearchEventSourceCoverageRotationSignal,
        module.ResearchEventSourceCoverageRotationRow,
        module.ResearchEventSourceCoverageRotationReasonCodeCount,
        module.ResearchEventSourceCoverageRotationReport,
    ):
        assert is_dataclass(public_type)
        assert all("float" not in str(field.type) for field in fields(public_type))
        assert all(
            "int" not in str(field.type) and field.type is not int
            for field in fields(public_type)
        )

    numeric_public_fragments = {
        "seconds",
        "count",
        "score",
        "available",
        "ratio",
    }
    for item in (cfg, source, result, result.rows[0], result.reason_code_counts[0]):
        for field_name, value in asdict(item).items():
            if field_name in {"reason_code_counts", "reason_codes", "rows"}:
                continue
            if any(fragment in field_name for fragment in numeric_public_fragments):
                assert type(value) is Decimal, (field_name, type(value))
                assert value.as_tuple().exponent == -6

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchEventSourceCoverageRotationSignal(
            **{**asdict(source), "paper_only": False},
        )
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(result.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result.reason_code_counts[0], report_only=False)


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (lambda: config(fresh_source_max_age_seconds=_DecimalSubclass("1.000000")), "Decimal"),
        (lambda: config(minimum_source_class_count=2), "Decimal"),
        (lambda: config(block_catalyst_pressure_score=d("0.500000")), "block_catalyst"),
        (lambda: signal(event_domain=_StringSubclass("macro_release")), "event_domain"),
        (lambda: signal(source_class="source_id_123"), "source_class"),
        (lambda: signal(event_domain="market_slug_weather"), "event_domain"),
        (lambda: signal(observed_at=_DatetimeSubclass(2026, 7, 8, tzinfo=UTC)), "observed_at"),
        (
            lambda: signal(observed_at=datetime(2026, 7, 8, tzinfo=_NoneOffsetTzinfo())),
            "timezone-aware",
        ),
        (lambda: signal(aggregate_source_count=d("1.500000")), "integer Decimal count"),
        (lambda: signal(reliability_memory_score=d("1.500000")), "reliability_memory_score"),
        (lambda: signal(catalyst_pressure_score=50), "catalyst_pressure_score"),
    ),
)
def test_validates_inputs(factory: object, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        factory()


def test_rejects_subclasses_duplicates_future_inputs_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(TypeError, match="subclassing"):
        type("ConfigSubclass", (module.ResearchEventSourceCoverageRotationConfig,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("SignalSubclass", (module.ResearchEventSourceCoverageRotationSignal,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("RowSubclass", (module.ResearchEventSourceCoverageRotationRow,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "ReasonCodeCountSubclass",
            (module.ResearchEventSourceCoverageRotationReasonCodeCount,),
            {},
        )
    with pytest.raises(TypeError, match="subclassing"):
        type("ReportSubclass", (module.ResearchEventSourceCoverageRotationReport,), {})

    with pytest.raises(ValueError, match="timezone-aware"):
        report(signal(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(
            signal(),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTzinfo()),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique event domain source class pairs"):
        report(signal(), signal())

    good = mixed_report()
    with pytest.raises(ValueError, match="reason_codes"):
        replace(good, reason_codes=("unexpected",))
    with pytest.raises(ValueError, match="domain_count"):
        replace(good, domain_count=d("99.000000"))
    with pytest.raises(ValueError, match="rows must be ranked"):
        replace(good, rows=tuple(reversed(good.rows)))
    with pytest.raises(ValueError, match="reason_code_counts must be ranked"):
        replace(good, reason_code_counts=tuple(reversed(good.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_codes must be ranked"):
        replace(good, reason_codes=tuple(reversed(good.reason_codes)))
    with pytest.raises(ValueError, match="reason_codes must be ranked"):
        replace(good.rows[0], reason_codes=tuple(reversed(good.rows[0].reason_codes)))


def test_module_scope_is_pure_report_only_and_has_no_forbidden_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_source_coverage_rotation_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "exchange mutation",
        "private_key",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "database",
        "durable",
        "store",
        "open(",
        "buy",
        "sell",
        "recommend",
        "position sizing",
        "live execution",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_dataclass_helpers = {"asdict"}
    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
        "pathlib",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "float",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
            assert all(
                alias.name not in forbidden_dataclass_helpers
                for alias in node.names
            )
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in {*forbidden_call_names, *forbidden_dataclass_helpers}
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
