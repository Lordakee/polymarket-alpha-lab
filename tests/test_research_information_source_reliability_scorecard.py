from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab import research_information_source_reliability_scorecard as module


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_information_source_reliability_scorecard.py"
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedSourceShape:
    public_source_label: str
    official_source_score: Decimal
    freshness_lag_seconds: Decimal
    independent_source_count: Decimal
    conflict_signal_count: Decimal
    agent_reach_fetch_quality: Decimal
    scrapling_fetch_quality: Decimal
    reason_codes: tuple[str, ...] = ()
    raw_candidate_id: str = "candidate-secret-123"
    market_id: str = "market-secret-456"
    market_slug: str = "private-slug"
    market_question: str = "private question"
    source_url: str = "https://hidden.example/source"
    source_text: str = "hidden source text"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> module.ResearchInformationSourceReliabilityScorecardConfig:
    values: dict[str, object] = {
        "config_version": "research-information-source-reliability-scorecard-v1",
        "ready_official_source_score": d("0.800000"),
        "attention_official_source_score": d("0.500000"),
        "ready_freshness_lag_seconds": d("3600.000000"),
        "blocker_freshness_lag_seconds": d("172800.000000"),
        "ready_independent_source_count": d("3.000000"),
        "attention_independent_source_count": d("2.000000"),
        "attention_conflict_signal_count": d("1.000000"),
        "blocker_conflict_signal_count": d("3.000000"),
        "ready_fetch_quality": d("0.800000"),
        "blocker_fetch_quality": d("0.500000"),
        "ready_reliability_score": d("0.800000"),
        "attention_reliability_score": d("0.600000"),
        "official_weight": d("0.200000"),
        "freshness_weight": d("0.200000"),
        "independence_weight": d("0.200000"),
        "conflict_weight": d("0.200000"),
        "fetch_quality_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchInformationSourceReliabilityScorecardConfig(**values)


def source_input(
    public_source_label: str = "official_event_feed",
    *,
    official_source_score: Decimal = d("1.000000"),
    freshness_lag_seconds: Decimal = d("900.000000"),
    independent_source_count: Decimal = d("4.000000"),
    conflict_signal_count: Decimal = d("0.000000"),
    agent_reach_fetch_quality: Decimal = d("0.950000"),
    scrapling_fetch_quality: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> module.ResearchInformationSourceReliabilityScorecardInput:
    return module.ResearchInformationSourceReliabilityScorecardInput(
        public_source_label=public_source_label,
        official_source_score=official_source_score,
        freshness_lag_seconds=freshness_lag_seconds,
        independent_source_count=independent_source_count,
        conflict_signal_count=conflict_signal_count,
        agent_reach_fetch_quality=agent_reach_fetch_quality,
        scrapling_fetch_quality=scrapling_fetch_quality,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *sources: object,
    cfg: module.ResearchInformationSourceReliabilityScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> module.ResearchInformationSourceReliabilityScorecardReport:
    return module.build_research_information_source_reliability_scorecard(
        sources,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if type(value) is dict:
        for key, item in value.items():
            values.extend(walk_values(key))
            values.extend(walk_values(item))
    elif type(value) is list:
        for item in value:
            values.extend(walk_values(item))
    return tuple(values)


def assert_public_payload_decimal_strings(payload: dict[str, Any]) -> None:
    assert not any(type(value) in (int, float, Decimal) for value in walk_values(payload))


def assert_dataclass_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            assert getattr(value, field.name) is True
            continue
        field_value = getattr(value, field.name)
        if field.name in {
            "config_version",
            "derived_validation_digest",
            "generated_at",
            "public_source_label",
            "reason_code",
            "reason_codes",
            "source_label",
            "source_priority_sequence",
            "status",
        }:
            continue
        if type(field_value) is tuple:
            continue
        if field_value is not None:
            assert type(field_value) is Decimal, field.name


def test_source_reliability_scorecard_rolls_ready_attention_blocker_rows() -> None:
    scorecard = build_report(
        source_input("official_event_feed"),
        source_input(
            "delayed_crosscheck_feed",
            official_source_score=d("0.700000"),
            freshness_lag_seconds=d("90000.000000"),
            independent_source_count=d("2.000000"),
            conflict_signal_count=d("1.000000"),
            agent_reach_fetch_quality=d("0.700000"),
            scrapling_fetch_quality=d("0.800000"),
            reason_codes=("analyst_checked",),
        ),
        source_input(
            "conflicting_social_feed",
            official_source_score=d("0.200000"),
            freshness_lag_seconds=d("300000.000000"),
            independent_source_count=d("1.000000"),
            conflict_signal_count=d("3.000000"),
            agent_reach_fetch_quality=d("0.400000"),
            scrapling_fetch_quality=d("0.300000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert type(scorecard) is module.ResearchInformationSourceReliabilityScorecardReport
    assert is_dataclass(scorecard)
    assert scorecard.generated_at == GENERATED_AT
    assert scorecard.generated_at.tzinfo is UTC
    assert module.STATUSES == ("ready", "attention", "blocker")
    assert scorecard.status == "blocker"
    assert scorecard.source_count == d("3.000000")
    assert scorecard.ready_count == d("1.000000")
    assert scorecard.attention_count == d("1.000000")
    assert scorecard.blocker_count == d("1.000000")
    assert scorecard.attention_or_blocker_count == d("2.000000")
    assert scorecard.average_reliability_score == d("0.597069")
    assert scorecard.minimum_fetch_quality_score == d("0.300000")
    assert scorecard.maximum_freshness_lag_seconds == d("300000.000000")

    assert tuple(row.source_label for row in scorecard.rows) == (
        "conflicting_social_feed",
        "delayed_crosscheck_feed",
        "official_event_feed",
    )
    assert tuple(row.status for row in scorecard.rows) == (
        "blocker",
        "attention",
        "ready",
    )

    blocker, attention, ready = scorecard.rows
    assert ready.reliability_score == d("0.980000")
    assert ready.fetch_quality_score == d("0.900000")
    assert ready.reason_codes == (
        "agent_reach_fetch_quality_ready",
        "conflict_signals_ready",
        "freshness_ready",
        "independent_sources_ready",
        "official_source_ready",
        "scrapling_fetch_quality_ready",
        "source_reliability_ready",
    )

    assert attention.freshness_score == d("0.489362")
    assert attention.independence_score == d("0.666667")
    assert attention.conflict_score == d("0.666667")
    assert attention.fetch_quality_score == d("0.700000")
    assert attention.reliability_score == d("0.644539")
    assert attention.reason_codes == (
        "agent_reach_fetch_quality_attention",
        "conflict_signals_attention",
        "freshness_attention",
        "independent_sources_attention",
        "input_analyst_checked",
        "official_source_attention",
        "scrapling_fetch_quality_ready",
        "source_reliability_attention",
    )

    assert blocker.freshness_score == d("0.000000")
    assert blocker.independence_score == d("0.333333")
    assert blocker.conflict_score == d("0.000000")
    assert blocker.fetch_quality_score == d("0.300000")
    assert blocker.reliability_score == d("0.166667")
    assert blocker.reason_codes == (
        "agent_reach_fetch_quality_blocker",
        "conflict_signals_blocker",
        "freshness_blocker",
        "independent_sources_blocker",
        "official_source_blocker",
        "scrapling_fetch_quality_blocker",
        "source_reliability_blocker",
    )

    assert set(scorecard.reason_codes) == {
        reason_code for row in scorecard.rows for reason_code in row.reason_codes
    }


def test_empty_scorecard_blocks_as_report_only_public_summary() -> None:
    scorecard = build_report()

    assert scorecard.status == "blocker"
    assert scorecard.source_count == ZERO
    assert scorecard.ready_count == ZERO
    assert scorecard.attention_count == ZERO
    assert scorecard.blocker_count == ZERO
    assert scorecard.attention_or_blocker_count == ZERO
    assert scorecard.average_reliability_score is None
    assert scorecard.minimum_fetch_quality_score is None
    assert scorecard.maximum_freshness_lag_seconds == ZERO
    assert scorecard.rows == ()
    assert scorecard.reason_codes == ("source_reliability_no_inputs",)
    assert scorecard.paper_only is True
    assert scorecard.report_only is True
    assert scorecard.readonly is True


def test_payload_is_deterministic_sanitized_and_decimal_string_only() -> None:
    supplied = SuppliedSourceShape(
        public_source_label="agent_reach_crosscheck_feed",
        official_source_score=d("0.700000"),
        freshness_lag_seconds=d("1200.000000"),
        independent_source_count=d("4.000000"),
        conflict_signal_count=d("0.000000"),
        agent_reach_fetch_quality=d("0.850000"),
        scrapling_fetch_quality=d("0.820000"),
        reason_codes=("operator_reviewed",),
    )
    first = module.research_information_source_reliability_scorecard_payload(
        build_report(supplied, source_input("official_event_feed")),
    )
    second = module.research_information_source_reliability_scorecard_payload(
        build_report(source_input("official_event_feed"), supplied),
    )

    assert first == second
    assert first["source_count"] == "2.000000"
    assert first["rows"][0]["source_label"] == "agent_reach_crosscheck_feed"
    assert first["rows"][0]["fetch_quality_score"] == "0.820000"
    assert_public_payload_decimal_strings(first)
    assert module.validate_research_information_source_reliability_scorecard_payload(first)

    rendered = repr(first).lower()
    for forbidden in (
        supplied.raw_candidate_id,
        supplied.market_id,
        supplied.market_slug,
        supplied.market_question,
        supplied.source_url,
        supplied.source_text,
        "hidden.example",
        "https://",
        "market_slug",
        "source_url",
        "source_text",
        "trade",
        "order",
        "wallet",
    ):
        assert forbidden.lower() not in rendered

    tampered = dict(first)
    tampered["ready_count"] = "99.000000"
    with pytest.raises(ValueError, match="ready_count"):
        module.validate_research_information_source_reliability_scorecard_payload(tampered)


def test_frozen_decimal_only_exact_types_and_hard_flags_are_enforced() -> None:
    scorecard = build_report(source_input())
    row = scorecard.rows[0]

    assert module.ResearchInformationSourceReliabilityScorecardConfig.__dataclass_params__.frozen
    assert module.ResearchInformationSourceReliabilityScorecardInput.__dataclass_params__.frozen
    assert module.ResearchInformationSourceReliabilityRow.__dataclass_params__.frozen
    assert module.ResearchInformationSourceReliabilityScorecardReport.__dataclass_params__.frozen
    assert isinstance(config(), module.ResearchInformationSourceReliabilityScorecardConfig)
    assert isinstance(source_input(), module.ResearchInformationSourceReliabilityScorecardInput)
    assert isinstance(row, module.ResearchInformationSourceReliabilityRow)

    with pytest.raises(FrozenInstanceError):
        scorecard.status = "ready"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.reliability_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "DerivedConfig",
            (module.ResearchInformationSourceReliabilityScorecardConfig,),
            {},
        )

    with pytest.raises(ValueError, match="ready_official_source_score"):
        config(ready_official_source_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="blocker_freshness_lag_seconds"):
        config(blocker_freshness_lag_seconds=172800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="component weights"):
        config(fetch_quality_weight=d("0.100000"))
    with pytest.raises(ValueError, match="official_source_score"):
        source_input(official_source_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="freshness_lag_seconds"):
        source_input(freshness_lag_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="independent_source_count"):
        source_input(independent_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="conflict_signal_count"):
        source_input(conflict_signal_count=d("-1.000000"))
    with pytest.raises(ValueError, match="agent_reach_fetch_quality"):
        source_input(agent_reach_fetch_quality=d("1.000001"))
    with pytest.raises(ValueError, match="scrapling_fetch_quality"):
        source_input(scrapling_fetch_quality=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        source_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(scorecard, readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(source_input(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    for value in (
        "raw-candidate-123",
        "event-market-id",
        "market_slug_value",
        "question_value",
        "source-url-value",
        "https://hidden.example/source",
        "source-text-value",
        "dsn-value",
        "table-value",
        "token-value",
        "wallet-value",
        "order-value",
        "trade-value",
        "position-value",
        "buy-value",
        "sell-value",
        "recommend-value",
    ):
        with pytest.raises(ValueError, match="protected public material"):
            source_input(public_source_label=value)

    assert_dataclass_numeric_fields_are_decimal(config())
    assert_dataclass_numeric_fields_are_decimal(source_input())
    assert_dataclass_numeric_fields_are_decimal(row)
    assert_dataclass_numeric_fields_are_decimal(scorecard)


def test_report_and_row_consistency_reject_manual_drift() -> None:
    scorecard = build_report(source_input("b_feed"), source_input("a_feed"))
    row = scorecard.rows[0]

    with pytest.raises(ValueError, match="status"):
        replace(row, status="attention")
    with pytest.raises(ValueError, match="fetch_quality_score"):
        replace(row, fetch_quality_score=d("0.100000"))
    with pytest.raises(ValueError, match="reliability_score"):
        replace(row, reliability_score=d("0.100000"))
    with pytest.raises(ValueError, match="rows"):
        replace(scorecard, rows=tuple(reversed(scorecard.rows)))
    with pytest.raises(ValueError, match="ready_count"):
        replace(scorecard, ready_count=ZERO)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(scorecard, reason_codes=("source_reliability_attention",))


def test_module_is_pure_report_only_with_no_io_network_or_database_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_roots: set[str] = set()
    call_names: set[str] = set()
    attribute_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    assert not imported_roots & {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
    }
    assert not call_names & {
        "__import__",
        "connect",
        "execute",
        "open",
        "request",
        "urlopen",
        "write",
        "write_bytes",
        "write_text",
    }
    assert not attribute_names & {"connect", "execute", "write", "write_bytes", "write_text"}

    lowered = source.lower()
    for value in (
        "live_trading",
        "wallet",
        "broker",
        "order",
        "private_key",
        "api_key",
        "secret",
        "position",
        "database",
        "network",
        "durable",
    ):
        assert value not in lowered
