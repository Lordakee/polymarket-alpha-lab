from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_retrieval_completeness_gate_report import (
    ResearchSourceRetrievalCompletenessClassRow,
    ResearchSourceRetrievalCompletenessGateConfig,
    ResearchSourceRetrievalCompletenessGateReport,
    ResearchSourceRetrievalSourceClassAggregate,
    build_research_source_retrieval_completeness_gate_report,
    research_source_retrieval_completeness_gate_report_payload,
    validate_research_source_retrieval_completeness_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceRetrievalCompletenessGateConfig:
    values = {
        "config_version": "research-source-retrieval-completeness-gate-report-v0",
        "minimum_class_coverage_ratio": d("1.000000"),
        "block_class_coverage_ratio": d("0.500000"),
        "watch_stale_source_ratio": d("0.250000"),
        "block_stale_source_ratio": d("0.600000"),
        "watch_failed_retrieval_ratio": d("0.250000"),
        "block_failed_retrieval_ratio": d("0.500000"),
        "watch_recheck_urgency_ratio": d("0.250000"),
        "block_recheck_urgency_ratio": d("0.600000"),
    }
    values.update(overrides)
    return ResearchSourceRetrievalCompletenessGateConfig(**values)


def source_class(
    name: str,
    *,
    required: str,
    attempted: str,
    retrieved: str,
    stale: str = "0.000000",
    failed: str = "0.000000",
    pending_recheck: str = "0.000000",
) -> ResearchSourceRetrievalSourceClassAggregate:
    return ResearchSourceRetrievalSourceClassAggregate(
        source_class=name,
        required_source_count=d(required),
        retrieval_attempt_count=d(attempted),
        retrieved_source_count=d(retrieved),
        stale_source_count=d(stale),
        failed_retrieval_count=d(failed),
        pending_recheck_count=d(pending_recheck),
    )


def report(
    rows: tuple[ResearchSourceRetrievalSourceClassAggregate, ...],
    *,
    cfg: ResearchSourceRetrievalCompletenessGateConfig | None = None,
) -> ResearchSourceRetrievalCompletenessGateReport:
    return build_research_source_retrieval_completeness_gate_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_empty_input_blocks_with_zero_aggregate_pressure() -> None:
    completeness_report = report(())

    assert type(completeness_report) is ResearchSourceRetrievalCompletenessGateReport
    assert completeness_report.generated_at == GENERATED_AT
    assert completeness_report.config_version == (
        "research-source-retrieval-completeness-gate-report-v0"
    )
    assert completeness_report.source_class_count == d("0.000000")
    assert completeness_report.required_source_count == d("0.000000")
    assert completeness_report.retrieved_source_count == d("0.000000")
    assert completeness_report.pass_count == d("0.000000")
    assert completeness_report.watch_count == d("0.000000")
    assert completeness_report.block_count == d("0.000000")
    assert completeness_report.source_class_coverage_ratio == d("0.000000")
    assert completeness_report.retrieval_coverage_ratio == d("0.000000")
    assert completeness_report.stale_source_ratio == d("0.000000")
    assert completeness_report.failed_retrieval_pressure_ratio == d("0.000000")
    assert completeness_report.recheck_urgency_ratio == d("0.000000")
    assert completeness_report.status == "block"
    assert completeness_report.reason_codes == ("no_retrieval_source_classes",)
    assert completeness_report.rows == ()
    assert completeness_report.paper_only is True
    assert completeness_report.report_only is True
    assert completeness_report.readonly is True
    assert len(completeness_report.derived_validation_digest) == 64


def test_complete_fresh_source_class_coverage_passes_with_deterministic_payload() -> None:
    completeness_report = report(
        (
            source_class(
                "corroborating",
                required="2.000000",
                attempted="2.000000",
                retrieved="2.000000",
            ),
            source_class(
                "official",
                required="2.000000",
                attempted="2.000000",
                retrieved="2.000000",
            ),
            source_class(
                "statistical",
                required="2.000000",
                attempted="2.000000",
                retrieved="2.000000",
            ),
        ),
    )

    payload = research_source_retrieval_completeness_gate_report_payload(
        completeness_report,
    )
    repeat_payload = research_source_retrieval_completeness_gate_report_payload(
        completeness_report,
    )

    assert completeness_report.status == "pass"
    assert completeness_report.source_class_count == d("3.000000")
    assert completeness_report.covered_source_class_count == d("3.000000")
    assert completeness_report.required_source_count == d("6.000000")
    assert completeness_report.retrieval_attempt_count == d("6.000000")
    assert completeness_report.retrieved_source_count == d("6.000000")
    assert completeness_report.pass_count == d("3.000000")
    assert completeness_report.source_class_coverage_ratio == d("1.000000")
    assert completeness_report.retrieval_coverage_ratio == d("1.000000")
    assert completeness_report.reason_codes == ("retrieval_completeness_pass",)
    assert tuple(row.source_class for row in completeness_report.rows) == (
        "corroborating",
        "official",
        "statistical",
    )
    assert all(type(row) is ResearchSourceRetrievalCompletenessClassRow for row in completeness_report.rows)
    assert all(row.status == "pass" for row in completeness_report.rows)
    assert payload == repeat_payload
    assert payload["derived_validation_digest"] == (
        completeness_report.derived_validation_digest
    )
    assert payload["rows"][0]["retrieval_coverage_ratio"] == "1.000000"
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))
    assert json.dumps(payload, sort_keys=True) == json.dumps(repeat_payload, sort_keys=True)
    assert validate_research_source_retrieval_completeness_gate_report_payload(payload)


def test_stale_failed_and_recheck_pressure_drive_watch_and_block_statuses() -> None:
    completeness_report = report(
        (
            source_class(
                "official",
                required="3.000000",
                attempted="5.000000",
                retrieved="2.000000",
                stale="1.000000",
                failed="1.000000",
                pending_recheck="1.000000",
            ),
            source_class(
                "corroborating",
                required="4.000000",
                attempted="4.000000",
                retrieved="1.000000",
                stale="1.000000",
                failed="3.000000",
                pending_recheck="1.000000",
            ),
        ),
    )

    assert completeness_report.status == "block"
    assert completeness_report.source_class_count == d("2.000000")
    assert completeness_report.covered_source_class_count == d("0.000000")
    assert completeness_report.required_source_count == d("7.000000")
    assert completeness_report.retrieval_attempt_count == d("9.000000")
    assert completeness_report.retrieved_source_count == d("3.000000")
    assert completeness_report.stale_source_count == d("2.000000")
    assert completeness_report.failed_retrieval_count == d("4.000000")
    assert completeness_report.pending_recheck_count == d("2.000000")
    assert completeness_report.watch_count == d("1.000000")
    assert completeness_report.block_count == d("1.000000")
    assert completeness_report.source_class_coverage_ratio == d("0.000000")
    assert completeness_report.retrieval_coverage_ratio == d("0.428571")
    assert completeness_report.stale_source_ratio == d("0.666667")
    assert completeness_report.failed_retrieval_pressure_ratio == d("0.444444")
    assert completeness_report.recheck_urgency_ratio == d("0.666667")
    assert completeness_report.reason_codes == (
        "failed_retrieval_pressure_watch",
        "recheck_urgency_block",
        "source_class_coverage_block",
        "stale_source_concentration_block",
    )

    corroborating, official = completeness_report.rows
    assert (corroborating.source_class, corroborating.status) == ("corroborating", "block")
    assert (official.source_class, official.status) == ("official", "watch")
    assert corroborating.reason_codes == (
        "failed_retrieval_pressure_block",
        "recheck_urgency_block",
        "source_class_coverage_block",
        "stale_source_concentration_block",
    )
    assert official.reason_codes == (
        "failed_retrieval_pressure_pass",
        "recheck_urgency_watch",
        "source_class_coverage_watch",
        "stale_source_concentration_watch",
    )


def test_validation_rejects_bad_numeric_types_inconsistent_counts_flags_and_surfaces() -> None:
    with pytest.raises(ValueError, match="minimum_class_coverage_ratio"):
        config(minimum_class_coverage_ratio=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_stale_source_ratio"):
        config(watch_stale_source_ratio=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="block_class_coverage_ratio"):
        config(block_class_coverage_ratio=d("1.000000"))
    with pytest.raises(ValueError, match="source_class"):
        source_class(
            "raw-url-leak",
            required="1.000000",
            attempted="1.000000",
            retrieved="1.000000",
        )
    with pytest.raises(ValueError, match="source_class"):
        source_class(
            "market_id_leak",
            required="1.000000",
            attempted="1.000000",
            retrieved="1.000000",
        )
    with pytest.raises(ValueError, match="required_source_count"):
        source_class(
            "official",
            required="0.000000",
            attempted="1.000000",
            retrieved="1.000000",
        )
    with pytest.raises(ValueError, match="failed_retrieval_count"):
        source_class(
            "official",
            required="1.000000",
            attempted="1.000000",
            retrieved="1.000000",
            failed="2.000000",
        )
    with pytest.raises(ValueError, match="stale_source_count"):
        source_class(
            "official",
            required="1.000000",
            attempted="1.000000",
            retrieved="1.000000",
            stale="2.000000",
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            source_class(
                "official",
                required="1.000000",
                attempted="1.000000",
                retrieved="1.000000",
            ),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        validate_research_source_retrieval_completeness_gate_report_payload(
            {
                "raw_url": "https://example.invalid",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    completeness_report = report(
        (
            source_class(
                "official",
                required="1.000000",
                attempted="1.000000",
                retrieved="1.000000",
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        completeness_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        completeness_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(completeness_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="pass_count"):
        replace(completeness_report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(completeness_report, derived_validation_digest="0" * 64)


def test_owned_module_has_no_external_or_trading_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_retrieval_completeness_gate_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "raw_url",
        "source_text",
        "market_id",
        "question",
        "database",
        "network",
        "trade",
        "trading",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
