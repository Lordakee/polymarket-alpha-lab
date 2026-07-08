import ast
import json
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_evidence_weighting_dashboard import (
    ResearchStrategyEvidenceSignal,
    ResearchStrategyEvidenceWeightingConfig,
    ResearchStrategyEvidenceWeightingReasonCodeCount,
    ResearchStrategyEvidenceWeightingReport,
    ResearchStrategyEvidenceWeightingRow,
    build_research_strategy_evidence_weighting_dashboard,
    research_strategy_evidence_weighting_dashboard_digest,
    research_strategy_evidence_weighting_dashboard_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_evidence_weighting_dashboard.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    research_key: str = "alpha.research.one",
    *,
    evidence_strength: Decimal = d("0.900000"),
    source_reliability: Decimal = d("0.900000"),
    conflict_rate: Decimal = d("0.100000"),
    freshness_score: Decimal = d("0.900000"),
    team_confidence: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyEvidenceSignal:
    return ResearchStrategyEvidenceSignal(
        research_key=research_key,
        evidence_strength=evidence_strength,
        source_reliability=source_reliability,
        conflict_rate=conflict_rate,
        freshness_score=freshness_score,
        team_confidence=team_confidence,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**kwargs: object) -> ResearchStrategyEvidenceWeightingConfig:
    return ResearchStrategyEvidenceWeightingConfig(**kwargs)


def report(
    signals: tuple[ResearchStrategyEvidenceSignal, ...],
    *,
    cfg: ResearchStrategyEvidenceWeightingConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyEvidenceWeightingReport:
    return build_research_strategy_evidence_weighting_dashboard(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for entry in value.values() for item in walk_values(entry))
    if isinstance(value, list):
        return tuple(item for entry in value for item in walk_values(entry))
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field_name, field_value in asdict(value).items():
        if field_name in {"paper_only", "report_only", "readonly"}:
            continue
        if isinstance(field_value, tuple):
            continue
        if isinstance(field_value, str):
            continue
        if isinstance(field_value, datetime):
            continue
        assert type(field_value) is Decimal


def test_pass_watch_block_rows_and_summary_counts_are_public() -> None:
    summary = report(
        (
            signal("raw-candidate-id_market_slug_question_source-url-token-wallet-order-position-buy-sell"),
            signal(
                "alpha.research.watch",
                evidence_strength=d("0.650000"),
                source_reliability=d("0.600000"),
                conflict_rate=d("0.250000"),
                freshness_score=d("0.600000"),
                team_confidence=d("0.650000"),
            ),
            signal(
                "alpha.research.block",
                evidence_strength=d("0.900000"),
                source_reliability=d("0.900000"),
                conflict_rate=d("0.800000"),
                freshness_score=d("0.900000"),
                team_confidence=d("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.status == "block"
    assert summary.row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert sorted(row.status for row in summary.rows) == ["block", "pass", "watch"]
    assert {row.status for row in summary.rows} <= {"pass", "watch", "block"}
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    block_row = next(row for row in summary.rows if row.status == "block")
    assert block_row.reason_codes == (
        "research_strategy_evidence_weighting_high_conflict",
    )
    watch_row = next(row for row in summary.rows if row.status == "watch")
    assert watch_row.reason_codes == (
        "research_strategy_evidence_weighting_watch_weight",
    )
    pass_row = next(row for row in summary.rows if row.status == "pass")
    assert pass_row.reason_codes == ("research_strategy_evidence_weighting_pass",)

    public = repr(research_strategy_evidence_weighting_dashboard_payload(summary)).lower()
    for leaked in (
        "raw-candidate-id",
        "market_slug",
        "question",
        "source-url",
        "token",
        "wallet",
        "order",
        "position",
        "buy",
        "sell",
    ):
        assert leaked not in public


def test_empty_dashboard_blocks_without_rows() -> None:
    summary = report(())

    assert summary.status == "block"
    assert summary.row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_evidence_weight == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchStrategyEvidenceWeightingReasonCodeCount(
            reason_code="research_strategy_evidence_weighting_no_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_strategy_evidence_weighting_no_inputs",
    )


def test_decimal_and_exact_type_contracts_are_rejected() -> None:
    assert is_dataclass(ResearchStrategyEvidenceWeightingConfig)
    assert is_dataclass(ResearchStrategyEvidenceSignal)
    assert is_dataclass(ResearchStrategyEvidenceWeightingRow)
    assert is_dataclass(ResearchStrategyEvidenceWeightingReasonCodeCount)
    assert is_dataclass(ResearchStrategyEvidenceWeightingReport)

    cfg = config()
    source_signal = signal()
    summary = report((source_signal,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.pass_weight_threshold = d("0.800000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_signal.evidence_strength = d("0.800000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].evidence_weight = d("0.800000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("research-strategy-v0"))
    with pytest.raises(ValueError, match="evidence_strength_weight"):
        config(evidence_strength_weight=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="component weights"):
        config(evidence_strength_weight=d("0.400000"))
    with pytest.raises(ValueError, match="pass_weight_threshold"):
        config(pass_weight_threshold=d("0.400000"))
    with pytest.raises(ValueError, match="max_conflict_rate"):
        config(max_conflict_rate=Decimal("NaN"))
    with pytest.raises(ValueError, match="research_key"):
        signal(_StringSubclass("alpha.research"))
    with pytest.raises(ValueError, match="evidence_strength"):
        signal(evidence_strength=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability"):
        signal(source_reliability=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="conflict_rate"):
        signal(conflict_rate=d("1.000001"))
    with pytest.raises(ValueError, match="freshness_score"):
        signal(freshness_score=d("-0.000001"))
    with pytest.raises(ValueError, match="team_confidence"):
        signal(team_confidence=Decimal("Infinity"))
    with pytest.raises(ValueError, match="generated_at"):
        report((signal(),), generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="signals"):
        report((object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="config"):
        build_research_strategy_evidence_weighting_dashboard(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )


def test_public_payload_uses_decimal_strings_and_stable_digest() -> None:
    summary = report(
        (
            signal("alpha.research.z"),
            signal(
                "alpha.research.a",
                evidence_strength=d("0.650000"),
                source_reliability=d("0.600000"),
                conflict_rate=d("0.250000"),
                freshness_score=d("0.600000"),
                team_confidence=d("0.650000"),
            ),
        ),
    )

    first_payload = research_strategy_evidence_weighting_dashboard_payload(summary)
    second_payload = research_strategy_evidence_weighting_dashboard_payload(summary)
    json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["average_evidence_weight"] == "0.770000"
    assert first_payload["public_report_digest"] == summary.public_report_digest
    assert (
        research_strategy_evidence_weighting_dashboard_digest(summary)
        == summary.public_report_digest
    )
    assert all(row["public_research_digest"].startswith("sha256:") for row in first_payload["rows"])
    assert not any(isinstance(value, float) for value in walk_values(first_payload))

    reordered = report((signal("alpha.research.a"), signal("alpha.research.z")))
    assert [
        row["public_research_digest"] for row in first_payload["rows"]
    ] == [
        row["public_research_digest"]
        for row in research_strategy_evidence_weighting_dashboard_payload(reordered)["rows"]
    ]


def test_public_leak_and_manual_drift_rejections() -> None:
    summary = report((signal(),))
    row = summary.rows[0]

    with pytest.raises(ValueError, match="public_research_digest"):
        replace(row, public_research_digest="raw-candidate-id")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row,
            reason_codes=(
                "research_strategy_evidence_weighting_pass",
                "research_strategy_evidence_weighting_watch_weight",
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(row, status="watch")
    with pytest.raises(ValueError, match="config_version"):
        replace(summary, config_version="market_slug")
    with pytest.raises(ValueError, match="pass_count"):
        replace(summary, pass_count=ZERO)
    with pytest.raises(ValueError, match="public_report_digest"):
        replace(summary, public_report_digest="sha256:0000000000000000")
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                signal("alpha.research.z"),
                signal("alpha.research.a"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_hard_flags_are_enforced_everywhere() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        signal(readonly=False)

    summary = report((signal(),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)


def test_report_digest_and_payload_consistency_for_each_status() -> None:
    for expected_status, rows in (
        ("pass", (signal("alpha.pass"),)),
        (
            "watch",
            (
                signal(
                    "alpha.watch",
                    evidence_strength=d("0.650000"),
                    source_reliability=d("0.600000"),
                    conflict_rate=d("0.250000"),
                    freshness_score=d("0.600000"),
                    team_confidence=d("0.650000"),
                ),
            ),
        ),
        (
            "block",
            (
                signal(
                    "alpha.block",
                    evidence_strength=d("0.200000"),
                    source_reliability=d("0.200000"),
                    conflict_rate=d("0.800000"),
                    freshness_score=d("0.200000"),
                    team_confidence=d("0.200000"),
                ),
            ),
        ),
    ):
        summary = report(rows)
        payload = research_strategy_evidence_weighting_dashboard_payload(summary)
        assert summary.status == expected_status
        assert payload["status"] == expected_status
        assert payload["public_report_digest"] == summary.public_report_digest
        assert (
            research_strategy_evidence_weighting_dashboard_digest(summary)
            == payload["public_report_digest"]
        )


def test_public_numeric_fields_are_decimals() -> None:
    source_signal = signal()
    summary = report((source_signal,))

    assert_decimal_numeric_fields(source_signal)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_execution_or_advice_surfaces() -> None:
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
        "advice",
        "market_slug",
        "market_id",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "position",
        "trade",
        "buy",
        "sell",
        "recommend",
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
