from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_outlier_detector import (
    DEFAULT_RESEARCH_MARKET_OUTLIER_DETECTOR_CONFIG_VERSION,
    ResearchMarketOutlierDetectorConfig,
    ResearchMarketOutlierDetectorInputRow,
    ResearchMarketOutlierDetectorReasonCodeCount,
    ResearchMarketOutlierDetectorReport,
    ResearchMarketOutlierDetectorRow,
    build_research_market_outlier_detector,
    research_market_outlier_detector_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path("src/polymarket_alpha_lab/research_market_outlier_detector.py")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def outlier_ref(candidate: str, market: str) -> str:
    digest = hashlib.sha256(f"{candidate}|{market}".encode("utf-8")).hexdigest()[:12]
    return f"outlier_{digest}"


def config(**overrides: object) -> ResearchMarketOutlierDetectorConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_MARKET_OUTLIER_DETECTOR_CONFIG_VERSION,
        "base_rate_drift_watch_threshold": d("0.100000"),
        "base_rate_drift_block_threshold": d("0.250000"),
        "attention_gap_watch_threshold": d("0.200000"),
        "attention_gap_block_threshold": d("0.400000"),
        "overreaction_watch_threshold": d("0.150000"),
        "overreaction_block_threshold": d("0.250000"),
        "evidence_quality_watch_floor": d("0.500000"),
        "evidence_quality_block_floor": d("0.300000"),
    }
    values.update(overrides)
    return ResearchMarketOutlierDetectorConfig(**values)


def input_row(
    raw_candidate_identifier: str = "candidate-alpha-123",
    raw_market_identifier: str = "market-live-slug-or-question?token=hidden",
    *,
    public_bucket: str = "macro_policy",
    base_rate_probability: Decimal = d("0.200000"),
    current_probability: Decimal = d("0.590000"),
    public_attention_score: Decimal = d("0.900000"),
    research_attention_score: Decimal = d("0.300000"),
    probability_move_score: Decimal = d("0.320000"),
    evidence_move_score: Decimal = d("0.050000"),
    evidence_quality_score: Decimal = d("0.220000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketOutlierDetectorInputRow:
    return ResearchMarketOutlierDetectorInputRow(
        raw_candidate_identifier=raw_candidate_identifier,
        raw_market_identifier=raw_market_identifier,
        public_bucket=public_bucket,
        base_rate_probability=base_rate_probability,
        current_probability=current_probability,
        public_attention_score=public_attention_score,
        research_attention_score=research_attention_score,
        probability_move_score=probability_move_score,
        evidence_move_score=evidence_move_score,
        evidence_quality_score=evidence_quality_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchMarketOutlierDetectorConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketOutlierDetectorReport:
    return build_research_market_outlier_detector(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal
        if field.name.endswith(("_count", "_score", "_rate", "_gap", "_drift")):
            assert type(item) is Decimal


def test_detector_combines_outlier_signals_redacts_rows_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "candidate-gamma-789",
                "market-passive-public-detail",
                public_bucket="macro_passive",
                base_rate_probability=d("0.500000"),
                current_probability=d("0.540000"),
                public_attention_score=d("0.410000"),
                research_attention_score=d("0.390000"),
                probability_move_score=d("0.060000"),
                evidence_move_score=d("0.050000"),
                evidence_quality_score=d("0.850000"),
            ),
            input_row(
                "candidate-beta-456",
                "market-watch-slug",
                public_bucket="macro_watch",
                base_rate_probability=d("0.510000"),
                current_probability=d("0.640000"),
                public_attention_score=d("0.780000"),
                research_attention_score=d("0.530000"),
                probability_move_score=d("0.180000"),
                evidence_move_score=d("0.060000"),
                evidence_quality_score=d("0.450000"),
            ),
            input_row(),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_RESEARCH_MARKET_OUTLIER_DETECTOR_CONFIG_VERSION
    assert summary.report_status == "block"
    assert summary.report_action == "block_report_only_research_market_outlier_detector"
    assert summary.input_count == d("3.000000")
    assert summary.outlier_count == d("2.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.base_rate_drift_count == d("2.000000")
    assert summary.attention_gap_count == d("2.000000")
    assert summary.crowd_overreaction_count == d("1.000000")
    assert summary.low_evidence_quality_count == d("2.000000")
    assert summary.max_anomaly_score == d("0.510000")
    assert summary.average_evidence_quality_score == d("0.506667")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.public_bucket, row.row_status) for row in summary.rows) == (
        ("macro_policy", "block"),
        ("macro_watch", "watch"),
        ("macro_passive", "pass"),
    )

    blocked = summary.rows[0]
    assert blocked.outlier_ref == outlier_ref(
        "candidate-alpha-123",
        "market-live-slug-or-question?token=hidden",
    )
    assert blocked.base_rate_drift == d("0.390000")
    assert blocked.attention_gap == d("0.600000")
    assert blocked.overreaction_score == d("0.270000")
    assert blocked.evidence_quality_gap == d("0.780000")
    assert blocked.anomaly_score == d("0.510000")
    assert blocked.redacted_outlier_reasons == (
        "research_market_outlier_detector_base_rate_drift",
        "research_market_outlier_detector_public_attention_gap",
        "research_market_outlier_detector_crowd_overreaction",
        "research_market_outlier_detector_low_evidence_quality",
    )

    watch = summary.rows[1]
    assert watch.outlier_ref == outlier_ref("candidate-beta-456", "market-watch-slug")
    assert watch.row_status == "watch"
    assert watch.anomaly_score == d("0.262500")
    assert watch.redacted_outlier_reasons == (
        "research_market_outlier_detector_base_rate_drift",
        "research_market_outlier_detector_public_attention_gap",
        "research_market_outlier_detector_low_evidence_quality",
    )

    passive = summary.rows[2]
    assert passive.row_status == "pass"
    assert passive.anomaly_score == d("0.055000")
    assert passive.redacted_outlier_reasons == (
        "research_market_outlier_detector_pass",
    )

    assert summary.reason_code_counts == (
        ResearchMarketOutlierDetectorReasonCodeCount(
            reason_code="research_market_outlier_detector_base_rate_drift",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        ),
        ResearchMarketOutlierDetectorReasonCodeCount(
            reason_code="research_market_outlier_detector_public_attention_gap",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        ),
        ResearchMarketOutlierDetectorReasonCodeCount(
            reason_code="research_market_outlier_detector_crowd_overreaction",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketOutlierDetectorReasonCodeCount(
            reason_code="research_market_outlier_detector_low_evidence_quality",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        ),
        ResearchMarketOutlierDetectorReasonCodeCount(
            reason_code="research_market_outlier_detector_pass",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(item.reason_code for item in summary.reason_code_counts)

    public = repr(asdict(summary)).lower()
    for token in (
        "candidate-alpha-123",
        "market-live-slug-or-question",
        "token",
        "hidden",
    ):
        assert token not in public


def test_empty_detector_report_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.report_status == "block"
    assert summary.report_action == "block_report_only_research_market_outlier_detector"
    assert summary.input_count == ZERO
    assert summary.outlier_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.max_anomaly_score == ZERO
    assert summary.average_evidence_quality_score == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchMarketOutlierDetectorReasonCodeCount(
            reason_code="research_market_outlier_detector_no_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == ("research_market_outlier_detector_no_inputs",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_uses_decimal_strings_and_leaks_no_raw_or_action_language() -> None:
    summary = report((input_row(),))
    payload = research_market_outlier_detector_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["input_count"] == "1.000000"
    assert payload["max_anomaly_score"] == "0.510000"
    assert payload["rows"][0]["current_probability"] == "0.590000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is int for value in walk_values(payload))
    assert not any(isinstance(value, float) for value in walk_values(payload))

    public = repr(payload).lower()
    for token in (
        "candidate-alpha-123",
        "market-live-slug-or-question",
        "question?",
        "token",
        "hidden",
        "https://",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "wallet",
        "auth",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert token not in public

    with pytest.raises(ValueError, match="unsafe"):
        research_market_outlier_detector_payload(
            {
                **payload,
                "token": "hidden",
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_market_outlier_detector_payload(
            {
                **payload,
                "rows": [{**payload["rows"][0], "public_bucket": "buy_now"}],
            },
        )


def test_public_contracts_frozen_dataclasses_exact_decimals_and_flags() -> None:
    assert is_dataclass(ResearchMarketOutlierDetectorConfig)
    assert is_dataclass(ResearchMarketOutlierDetectorInputRow)
    assert is_dataclass(ResearchMarketOutlierDetectorRow)
    assert is_dataclass(ResearchMarketOutlierDetectorReasonCodeCount)
    assert is_dataclass(ResearchMarketOutlierDetectorReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].current_probability = d("0.600000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("research-market-outlier-detector-v0"))
    with pytest.raises(ValueError, match="base_rate_drift_watch_threshold"):
        config(base_rate_drift_watch_threshold=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="base_rate_drift_block_threshold"):
        config(base_rate_drift_block_threshold=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="attention_gap_watch_threshold"):
        config(attention_gap_watch_threshold=Decimal("NaN"))
    with pytest.raises(ValueError, match="overreaction_block_threshold"):
        config(overreaction_watch_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="evidence_quality_block_floor"):
        config(evidence_quality_watch_floor=d("0.200000"))
    with pytest.raises(ValueError, match="public_bucket"):
        input_row(public_bucket=_StringSubclass("macro_policy"))
    with pytest.raises(ValueError, match="base_rate_probability"):
        input_row(base_rate_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="current_probability"):
        input_row(current_probability=d("1.000001"))
    with pytest.raises(ValueError, match="public_attention_score"):
        input_row(public_attention_score=d("-0.000001"))
    with pytest.raises(ValueError, match="research_attention_score"):
        input_row(research_attention_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="probability_move_score"):
        input_row(probability_move_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="evidence_quality_score"):
        input_row(evidence_quality_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_market_outlier_detector(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_market_outlier_detector(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))
    with pytest.raises(ValueError, match="duplicate"):
        report((input_row(), input_row()))


def test_derived_consistency_rejects_manual_drift() -> None:
    summary = report(
        (
            input_row(),
            input_row(
                "candidate-beta-456",
                "market-watch-slug",
                public_bucket="macro_watch",
                base_rate_probability=d("0.510000"),
                current_probability=d("0.640000"),
                public_attention_score=d("0.780000"),
                research_attention_score=d("0.530000"),
                probability_move_score=d("0.180000"),
                evidence_move_score=d("0.060000"),
                evidence_quality_score=d("0.450000"),
            ),
        ),
    )
    blocked = summary.rows[0]

    with pytest.raises(ValueError, match="base_rate_drift"):
        replace(blocked, base_rate_drift=d("0.999999"))
    with pytest.raises(ValueError, match="attention_gap"):
        replace(blocked, attention_gap=d("0.999999"))
    with pytest.raises(ValueError, match="overreaction_score"):
        replace(blocked, overreaction_score=d("0.999999"))
    with pytest.raises(ValueError, match="anomaly_score"):
        replace(blocked, anomaly_score=d("0.999999"))
    with pytest.raises(ValueError, match="row_status"):
        replace(blocked, row_status="pass")
    with pytest.raises(ValueError, match="redacted_outlier_reasons"):
        replace(
            blocked,
            redacted_outlier_reasons=(
                "research_market_outlier_detector_pass",
                "research_market_outlier_detector_base_rate_drift",
            ),
        )

    with pytest.raises(ValueError, match="input_count"):
        replace(summary, input_count=ZERO)
    with pytest.raises(ValueError, match="outlier_count"):
        replace(summary, outlier_count=ZERO)
    with pytest.raises(ValueError, match="max_anomaly_score"):
        replace(summary, max_anomaly_score=ZERO)
    with pytest.raises(ValueError, match="report_status"):
        replace(
            summary,
            report_status="pass",
            report_action="pass_report_only_research_market_outlier_detector",
        )
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))


def test_public_numeric_fields_are_exact_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_or_live_execution_surfaces() -> None:
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

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls
