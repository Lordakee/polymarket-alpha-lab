from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_information_source_reliability_scorecard import (
    ResearchInformationSourceReliabilityDigest,
    ResearchInformationSourceReliabilityReasonCodeCount,
    ResearchInformationSourceReliabilityRow,
    ResearchInformationSourceReliabilityScorecardConfig,
    ResearchInformationSourceReliabilityScorecardInput,
    ResearchInformationSourceReliabilityScorecardReport,
    build_research_information_source_reliability_scorecard,
    research_information_source_reliability_scorecard_digest,
    research_information_source_reliability_scorecard_payload,
)


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
    observed_latency_seconds: Decimal
    conflict_rate: Decimal
    historical_hit_rate: Decimal
    coverage_gap_rate: Decimal
    observation_count: Decimal
    hard_block_flag: bool = False
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


def config(**overrides: object) -> ResearchInformationSourceReliabilityScorecardConfig:
    values = {
        "config_version": "research-information-source-reliability-scorecard-v0",
        "pass_latency_seconds": d("3600"),
        "block_latency_seconds": d("86400"),
        "min_observation_count": d("3"),
        "pass_reliability_score": d("0.750000"),
        "watch_reliability_score": d("0.500000"),
        "block_conflict_rate": d("0.350000"),
        "block_coverage_gap_rate": d("0.500000"),
        "latency_weight": d("0.250000"),
        "conflict_weight": d("0.250000"),
        "history_weight": d("0.300000"),
        "coverage_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchInformationSourceReliabilityScorecardConfig(**values)


def source_input(
    public_source_label: str = "official_release_feed",
    *,
    observed_latency_seconds: Decimal = d("900"),
    conflict_rate: Decimal = d("0.000000"),
    historical_hit_rate: Decimal = d("0.920000"),
    coverage_gap_rate: Decimal = d("0.000000"),
    observation_count: Decimal = d("8"),
    hard_block_flag: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchInformationSourceReliabilityScorecardInput:
    return ResearchInformationSourceReliabilityScorecardInput(
        public_source_label=public_source_label,
        observed_latency_seconds=observed_latency_seconds,
        conflict_rate=conflict_rate,
        historical_hit_rate=historical_hit_rate,
        coverage_gap_rate=coverage_gap_rate,
        observation_count=observation_count,
        hard_block_flag=hard_block_flag,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchInformationSourceReliabilityScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchInformationSourceReliabilityScorecardReport:
    return build_research_information_source_reliability_scorecard(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def assert_decimal_numeric_fields(value: object) -> None:
    for field_name, field_value in asdict(value).items():
        if field_name in {"paper_only", "report_only", "readonly"}:
            assert field_value is True
        elif isinstance(field_value, tuple):
            continue
        elif field_name in {
            "config_version",
            "generated_at",
            "hard_block_flag",
            "manual_priority",
            "public_source_label",
            "reason_code",
            "source_label",
            "status",
        }:
            continue
        elif field_value is not None:
            assert type(field_value) is Decimal, field_name


def test_source_reliability_scorecard_pass_watch_block_rows_are_deterministic() -> None:
    scorecard = report(
        (
            source_input(
                "delayed_manual_feed",
                observed_latency_seconds=d("7200"),
                conflict_rate=d("0.100000"),
                historical_hit_rate=d("0.700000"),
                coverage_gap_rate=d("0.100000"),
                observation_count=d("5"),
                reason_codes=("analyst_checked",),
            ),
            source_input(
                "conflicting_blog_feed",
                observed_latency_seconds=d("1800"),
                conflict_rate=d("0.500000"),
                historical_hit_rate=d("0.650000"),
                coverage_gap_rate=d("0.100000"),
                observation_count=d("9"),
            ),
            source_input("official_release_feed"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert type(scorecard) is ResearchInformationSourceReliabilityScorecardReport
    assert scorecard.generated_at == GENERATED_AT
    assert scorecard.generated_at.tzinfo is UTC
    assert scorecard.config_version == "research-information-source-reliability-scorecard-v0"
    assert scorecard.source_count == d("3.000000")
    assert scorecard.pass_count == d("1.000000")
    assert scorecard.watch_count == d("1.000000")
    assert scorecard.block_count == d("1.000000")
    assert scorecard.status == "block"
    assert scorecard.average_reliability_score == d("0.860043")
    assert tuple((row.source_label, row.status, row.manual_priority) for row in scorecard.rows) == (
        ("official_release_feed", "pass", "primary_human_review"),
        ("delayed_manual_feed", "watch", "secondary_human_review"),
        ("conflicting_blog_feed", "block", "manual_escalation"),
    )

    passing = scorecard.rows[0]
    assert passing.reliability_score == d("0.976000")
    assert passing.latency_score == d("1.000000")
    assert passing.conflict_score == d("1.000000")
    assert passing.coverage_score == d("1.000000")
    assert passing.reason_codes == (
        "conflict_rate_pass",
        "coverage_gap_pass",
        "latency_pass",
        "reliability_score_pass",
        "source_reliability_pass",
    )

    watching = scorecard.rows[1]
    assert watching.reliability_score == d("0.854130")
    assert watching.latency_score == d("0.956522")
    assert watching.reason_codes == (
        "conflict_rate_watch",
        "coverage_gap_watch",
        "input_analyst_checked",
        "latency_watch",
        "reliability_score_pass",
        "source_reliability_watch",
    )

    blocking = scorecard.rows[2]
    assert blocking.reliability_score == d("0.750000")
    assert blocking.reason_codes == (
        "conflict_rate_block",
        "coverage_gap_watch",
        "latency_pass",
        "reliability_score_pass",
        "source_reliability_block",
    )
    assert set(scorecard.reason_codes) == {
        reason_code for row in scorecard.rows for reason_code in row.reason_codes
    }


def test_empty_scorecard_blocks_with_public_zero_counts() -> None:
    scorecard = report(())

    assert scorecard.status == "block"
    assert scorecard.source_count == ZERO
    assert scorecard.pass_count == ZERO
    assert scorecard.watch_count == ZERO
    assert scorecard.block_count == ZERO
    assert scorecard.average_reliability_score is None
    assert scorecard.rows == ()
    assert scorecard.reason_code_counts == (
        ResearchInformationSourceReliabilityReasonCodeCount(
            reason_code="source_reliability_no_inputs",
            count=d("1.000000"),
            source_ratio=d("1.000000"),
        ),
    )
    assert scorecard.reason_codes == ("source_reliability_no_inputs",)
    assert scorecard.paper_only is True
    assert scorecard.report_only is True
    assert scorecard.readonly is True


def test_decimal_and_type_contracts_reject_non_decimal_values() -> None:
    scorecard = report((source_input(),))

    assert isinstance(config(), ResearchInformationSourceReliabilityScorecardConfig)
    assert isinstance(source_input(), ResearchInformationSourceReliabilityScorecardInput)
    assert isinstance(scorecard.rows[0], ResearchInformationSourceReliabilityRow)
    assert isinstance(scorecard, ResearchInformationSourceReliabilityScorecardReport)
    assert isinstance(
        research_information_source_reliability_scorecard_digest(scorecard),
        ResearchInformationSourceReliabilityDigest,
    )

    with pytest.raises(FrozenInstanceError):
        scorecard.source_count = d("2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        scorecard.rows[0].reliability_score = d("0.1")  # type: ignore[misc]

    with pytest.raises(ValueError, match="pass_latency_seconds"):
        config(pass_latency_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_latency_seconds"):
        config(block_latency_seconds=_DecimalSubclass("86400"))
    with pytest.raises(ValueError, match="min_observation_count"):
        config(min_observation_count=d("1.5"))
    with pytest.raises(ValueError, match="pass_reliability_score"):
        config(pass_reliability_score=d("0.100000"))
    with pytest.raises(ValueError, match="component weights"):
        config(coverage_weight=d("0.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="public_source_label"):
        source_input(public_source_label="Official Feed")
    with pytest.raises(ValueError, match="observed_latency_seconds"):
        source_input(observed_latency_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="conflict_rate"):
        source_input(conflict_rate=d("1.000001"))
    with pytest.raises(ValueError, match="historical_hit_rate"):
        source_input(historical_hit_rate=Decimal("NaN"))
    with pytest.raises(ValueError, match="coverage_gap_rate"):
        source_input(coverage_gap_rate=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="observation_count"):
        source_input(observation_count=d("-1"))
    with pytest.raises(ValueError, match="hard_block_flag"):
        source_input(hard_block_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report((source_input(),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="config"):
        build_research_information_source_reliability_scorecard(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )


def test_public_payload_rejects_private_leaks_and_redacts_supplied_shapes() -> None:
    leaked_values = (
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
    )
    for value in leaked_values:
        with pytest.raises(ValueError, match="protected material"):
            source_input(public_source_label=value)

    supplied = SuppliedSourceShape(
        public_source_label="analyst_safe_feed",
        observed_latency_seconds=d("1200"),
        conflict_rate=d("0.000000"),
        historical_hit_rate=d("0.880000"),
        coverage_gap_rate=d("0.000000"),
        observation_count=d("11"),
    )
    scorecard = report((supplied,))
    payload = research_information_source_reliability_scorecard_payload(scorecard)
    payload_repr = repr(payload).lower()

    for value in (
        supplied.raw_candidate_id,
        supplied.market_id,
        supplied.market_slug,
        supplied.market_question,
        supplied.source_url,
        supplied.source_text,
        "hidden.example",
        "https://",
    ):
        assert value.lower() not in payload_repr
    assert payload["rows"][0]["source_label"] == "analyst_safe_feed"


def test_hard_block_flag_forces_public_block_status() -> None:
    scorecard = report(
        (
            source_input(
                "manual_override_feed",
                hard_block_flag=True,
                historical_hit_rate=d("0.990000"),
                observation_count=d("20"),
            ),
        ),
    )

    assert scorecard.status == "block"
    assert scorecard.block_count == d("1.000000")
    row = scorecard.rows[0]
    assert row.status == "block"
    assert row.manual_priority == "manual_escalation"
    assert row.reliability_score == d("0.997000")
    assert "hard_flag_block" in row.reason_codes
    assert set(row.reason_codes) <= set(scorecard.reason_codes)

    with pytest.raises(ValueError, match="paper_only"):
        ResearchInformationSourceReliabilityScorecardInput(
            public_source_label="unsafe_feed",
            observed_latency_seconds=d("900"),
            conflict_rate=d("0.000000"),
            historical_hit_rate=d("0.900000"),
            coverage_gap_rate=d("0.000000"),
            observation_count=d("8"),
            paper_only=False,
        )


def test_payload_is_decimal_string_only_and_deterministic() -> None:
    rows = (
        source_input("zeta_manual_feed", historical_hit_rate=d("0.800000")),
        source_input("alpha_manual_feed", historical_hit_rate=d("0.800000")),
    )
    first = research_information_source_reliability_scorecard_payload(report(rows))
    second = research_information_source_reliability_scorecard_payload(report(tuple(reversed(rows))))

    assert first == second
    json.dumps(first, sort_keys=True)
    assert first["source_count"] == "2.000000"
    assert first["rows"][0]["reliability_score"] == "0.940000"
    assert tuple(row["source_label"] for row in first["rows"]) == (
        "alpha_manual_feed",
        "zeta_manual_feed",
    )
    assert not any(isinstance(value, float) for value in walk_values(first))
    assert not any(isinstance(value, Decimal) for value in walk_values(first))
    assert {row["status"] for row in first["rows"]} <= {"pass", "watch", "block"}
    assert first["status"] in {"pass", "watch", "block"}


def test_report_and_digest_payloads_are_consistent() -> None:
    scorecard = report(
        (
            source_input("official_release_feed"),
            source_input(
                "slow_context_feed",
                observed_latency_seconds=d("40000"),
                conflict_rate=d("0.050000"),
                historical_hit_rate=d("0.700000"),
                coverage_gap_rate=d("0.050000"),
                observation_count=d("4"),
            ),
        ),
    )
    digest = research_information_source_reliability_scorecard_digest(scorecard)
    report_payload = research_information_source_reliability_scorecard_payload(scorecard)
    digest_payload = research_information_source_reliability_scorecard_payload(digest)

    for field_name in (
        "generated_at",
        "config_version",
        "source_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_reliability_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ):
        assert digest_payload[field_name] == report_payload[field_name]
    assert digest_payload["source_priority_sequence"] == [
        row["source_label"] for row in report_payload["rows"]
    ]
    assert digest.source_priority_sequence == tuple(row.source_label for row in scorecard.rows)


def test_report_and_row_consistency_reject_manual_drift() -> None:
    row = report((source_input(),)).rows[0]

    with pytest.raises(ValueError, match="manual_priority"):
        replace(row, manual_priority="manual_escalation")
    with pytest.raises(ValueError, match="conflict_score"):
        replace(row, conflict_score=d("0.500000"))
    with pytest.raises(ValueError, match="coverage_score"):
        replace(row, coverage_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    with pytest.raises(ValueError, match="reliability_score"):
        replace(row, status="pass", reliability_score=d("0.100000"))

    scorecard = report((source_input("b_feed"), source_input("a_feed")))
    with pytest.raises(ValueError, match="rows"):
        replace(scorecard, rows=tuple(reversed(scorecard.rows)))
    with pytest.raises(ValueError, match="pass_count"):
        replace(scorecard, pass_count=ZERO)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(scorecard, reason_codes=("source_reliability_watch",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(scorecard, paper_only=False)


def test_public_numeric_fields_are_decimals() -> None:
    source_row = source_input()
    scorecard = report((source_row,))
    digest = research_information_source_reliability_scorecard_digest(scorecard)

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(scorecard.rows[0])
    assert_decimal_numeric_fields(scorecard.reason_code_counts[0])
    assert_decimal_numeric_fields(scorecard)
    assert_decimal_numeric_fields(digest)


def test_module_has_no_io_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
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
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "market_slug",
        "question",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
        "database",
        "durable",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
