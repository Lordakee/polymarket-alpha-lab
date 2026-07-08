from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.research_team_specialist_memory_writeback_gate_report import (
    DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_WRITEBACK_GATE_REPORT_CONFIG_VERSION,
    SPECIALIST_MEMORY_WRITEBACK_GATE_STATUSES,
    ResearchTeamSpecialistMemoryWritebackGateConfig,
    ResearchTeamSpecialistMemoryWritebackGateInput,
    ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount,
    ResearchTeamSpecialistMemoryWritebackGateReport,
    ResearchTeamSpecialistMemoryWritebackGateRow,
    build_research_team_specialist_memory_writeback_gate_report,
    research_team_specialist_memory_writeback_gate_report_digest,
    research_team_specialist_memory_writeback_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_memory_writeback_gate_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchTeamSpecialistMemoryWritebackGateConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_WRITEBACK_GATE_REPORT_CONFIG_VERSION
        ),
        "min_pass_calibration_feedback_completeness_ratio": d("0.800000"),
        "min_watch_calibration_feedback_completeness_ratio": d("0.600000"),
        "min_pass_stale_thesis_label_ratio": d("0.750000"),
        "min_watch_stale_thesis_label_ratio": d("0.500000"),
        "min_pass_error_taxonomy_coverage_ratio": d("0.800000"),
        "min_watch_error_taxonomy_coverage_ratio": d("0.600000"),
        "max_pass_review_backlog_pressure": d("0.100000"),
        "max_watch_review_backlog_pressure": d("0.250000"),
    }
    values.update(overrides)
    return ResearchTeamSpecialistMemoryWritebackGateConfig(**values)


def input_item(
    specialist_label: str = "finance-crypto-specialist",
    category_label: str = "finance-crypto",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    outcome_learning_note_count: Decimal = d("10.000000"),
    calibration_feedback_complete_count: Decimal = d("9.000000"),
    stale_thesis_labeled_count: Decimal = d("8.000000"),
    error_taxonomy_tagged_count: Decimal = d("9.000000"),
    open_review_backlog_count: Decimal = d("0.000000"),
    high_priority_review_backlog_count: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamSpecialistMemoryWritebackGateInput:
    return ResearchTeamSpecialistMemoryWritebackGateInput(
        specialist_label=specialist_label,
        category_label=category_label,
        observed_at=observed_at,
        outcome_learning_note_count=outcome_learning_note_count,
        calibration_feedback_complete_count=calibration_feedback_complete_count,
        stale_thesis_labeled_count=stale_thesis_labeled_count,
        error_taxonomy_tagged_count=error_taxonomy_tagged_count,
        open_review_backlog_count=open_review_backlog_count,
        high_priority_review_backlog_count=high_priority_review_backlog_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchTeamSpecialistMemoryWritebackGateInput,
    cfg: ResearchTeamSpecialistMemoryWritebackGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamSpecialistMemoryWritebackGateReport:
    return build_research_team_specialist_memory_writeback_gate_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_empty_inputs_block_specialist_memory_writeback_readiness() -> None:
    gate = report()

    assert type(gate) is ResearchTeamSpecialistMemoryWritebackGateReport
    assert SPECIALIST_MEMORY_WRITEBACK_GATE_STATUSES == ("pass", "watch", "block")
    assert gate.generated_at == GENERATED_AT
    assert gate.config_version == (
        "research-team-specialist-memory-writeback-gate-report-v0"
    )
    assert gate.input_count == d("0.000000")
    assert gate.specialist_category_count == d("0.000000")
    assert gate.outcome_learning_note_count == d("0.000000")
    assert gate.calibration_feedback_complete_count == d("0.000000")
    assert gate.stale_thesis_labeled_count == d("0.000000")
    assert gate.error_taxonomy_tagged_count == d("0.000000")
    assert gate.open_review_backlog_count == d("0.000000")
    assert gate.high_priority_review_backlog_count == d("0.000000")
    assert gate.pass_count == d("0.000000")
    assert gate.watch_count == d("0.000000")
    assert gate.block_count == d("0.000000")
    assert gate.calibration_feedback_completeness_ratio == d("0.000000")
    assert gate.stale_thesis_label_ratio == d("0.000000")
    assert gate.error_taxonomy_coverage_ratio == d("0.000000")
    assert gate.review_backlog_pressure == d("0.000000")
    assert gate.writeback_readiness_score == d("0.000000")
    assert gate.status == "block"
    assert gate.next_review_step == "block_specialist_memory_writeback_until_review"
    assert gate.rows == ()
    assert gate.reason_codes == (
        "specialist_memory_writeback_no_outcome_learning_notes",
    )
    assert gate.reason_code_counts == (
        ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount(
            reason_code="specialist_memory_writeback_no_outcome_learning_notes",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert gate.paper_only is True
    assert gate.report_only is True
    assert gate.readonly is True
    assert len(gate.derived_validation_digest) == 64


def test_aggregate_readiness_scores_feedback_labels_taxonomy_and_backlog() -> None:
    gate = report(
        input_item(),
        input_item(
            "politics-specialist",
            "politics",
            calibration_feedback_complete_count=d("7.000000"),
            stale_thesis_labeled_count=d("6.000000"),
            error_taxonomy_tagged_count=d("7.000000"),
            open_review_backlog_count=d("2.000000"),
            high_priority_review_backlog_count=d("1.000000"),
        ),
        input_item(
            "sports-specialist",
            "sports-event-research",
            calibration_feedback_complete_count=d("5.000000"),
            stale_thesis_labeled_count=d("4.000000"),
            error_taxonomy_tagged_count=d("5.000000"),
            open_review_backlog_count=d("4.000000"),
            high_priority_review_backlog_count=d("2.000000"),
        ),
    )

    assert gate.input_count == d("3.000000")
    assert gate.specialist_category_count == d("3.000000")
    assert gate.outcome_learning_note_count == d("30.000000")
    assert gate.calibration_feedback_complete_count == d("21.000000")
    assert gate.stale_thesis_labeled_count == d("18.000000")
    assert gate.error_taxonomy_tagged_count == d("21.000000")
    assert gate.open_review_backlog_count == d("6.000000")
    assert gate.high_priority_review_backlog_count == d("3.000000")
    assert gate.pass_count == d("1.000000")
    assert gate.watch_count == d("1.000000")
    assert gate.block_count == d("1.000000")
    assert gate.calibration_feedback_completeness_ratio == d("0.700000")
    assert gate.stale_thesis_label_ratio == d("0.600000")
    assert gate.error_taxonomy_coverage_ratio == d("0.700000")
    assert gate.review_backlog_pressure == d("0.200000")
    assert gate.writeback_readiness_score == d("0.700000")
    assert gate.status == "block"
    assert gate.next_review_step == "block_specialist_memory_writeback_until_review"
    assert gate.reason_codes == (
        "specialist_memory_writeback_gate_block",
        "calibration_feedback_completeness_block",
        "stale_thesis_label_coverage_block",
        "error_taxonomy_coverage_block",
        "review_backlog_pressure_block",
        "calibration_feedback_completeness_watch",
        "stale_thesis_label_coverage_watch",
        "error_taxonomy_coverage_watch",
        "review_backlog_pressure_watch",
    )

    assert tuple(
        (row.specialist_label, row.category_label, row.status) for row in gate.rows
    ) == (
        ("finance-crypto-specialist", "finance-crypto", "pass"),
        ("politics-specialist", "politics", "watch"),
        ("sports-specialist", "sports-event-research", "block"),
    )
    passed, watched, blocked = gate.rows
    assert passed.writeback_readiness_score == d("0.900000")
    assert passed.reason_codes == (
        "specialist_memory_writeback_gate_pass",
        "manual_review_specialist_memory_writeback_pass",
    )
    assert watched.calibration_feedback_completeness_ratio == d("0.700000")
    assert watched.review_backlog_pressure == d("0.200000")
    assert watched.writeback_readiness_score == d("0.700000")
    assert watched.reason_codes == (
        "specialist_memory_writeback_gate_watch",
        "manual_review_specialist_memory_writeback_watch",
        "calibration_feedback_completeness_watch",
        "stale_thesis_label_coverage_watch",
        "error_taxonomy_coverage_watch",
        "review_backlog_pressure_watch",
    )
    assert blocked.calibration_feedback_completeness_ratio == d("0.500000")
    assert blocked.stale_thesis_label_ratio == d("0.400000")
    assert blocked.error_taxonomy_coverage_ratio == d("0.500000")
    assert blocked.review_backlog_pressure == d("0.400000")
    assert blocked.writeback_readiness_score == d("0.500000")
    assert blocked.reason_codes == (
        "specialist_memory_writeback_gate_block",
        "manual_review_specialist_memory_writeback_block",
        "calibration_feedback_completeness_block",
        "stale_thesis_label_coverage_block",
        "error_taxonomy_coverage_block",
        "review_backlog_pressure_block",
    )


def test_payload_digest_are_deterministic_decimal_string_only_and_public_safe() -> None:
    first = report(
        input_item(
            "sports-specialist",
            "sports-event-research",
            reason_codes=("taxonomy_review_complete", "quality_review_complete"),
        ),
        input_item("finance-crypto-specialist", "finance-crypto"),
    )
    second = report(
        input_item("finance-crypto-specialist", "finance-crypto"),
        input_item(
            "sports-specialist",
            "sports-event-research",
            reason_codes=("quality_review_complete", "taxonomy_review_complete"),
        ),
    )

    first_payload = research_team_specialist_memory_writeback_gate_report_payload(first)
    second_payload = research_team_specialist_memory_writeback_gate_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert research_team_specialist_memory_writeback_gate_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_count"] == "2.000000"
    assert first_payload["rows"][0]["specialist_label"] == "finance-crypto-specialist"
    assert first_payload["rows"][0]["writeback_readiness_score"] == "0.900000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "market_slug" not in encoded.lower()
    assert "source_id" not in encoded.lower()
    assert "wallet" not in encoded.lower()
    assert "question" not in encoded.lower()
    assert "raw" not in encoded.lower()
    assert not any(has_forbidden_public_surface_key(key) for key in walk_payload_keys(first_payload))

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_specialist_memory_writeback_gate_report_payload(tampered)

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_writeback_gate_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "specialist_label": "raw-specialist-label"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_writeback_gate_report_payload(unsafe_value)


def test_validation_freezing_flags_utc_decimal_only_and_consistency_checks() -> None:
    populated = report(input_item())

    assert populated.generated_at == GENERATED_AT
    assert populated.rows[0].observed_at == GENERATED_AT - timedelta(hours=1)
    assert populated.status in {"pass", "watch", "block"}
    assert all(row.status in {"pass", "watch", "block"} for row in populated.rows)

    for public_type in (
        ResearchTeamSpecialistMemoryWritebackGateConfig,
        ResearchTeamSpecialistMemoryWritebackGateInput,
        ResearchTeamSpecialistMemoryWritebackGateRow,
        ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount,
        ResearchTeamSpecialistMemoryWritebackGateReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for field in fields(public_type):
            if is_numeric_public_field(field.name):
                assert hints[field.name] is Decimal, (public_type.__name__, field.name)

    for value in (config(), input_item(), populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            if is_numeric_public_field(field.name):
                assert type(getattr(value, field.name)) is Decimal, field.name

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].writeback_readiness_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="min_pass_calibration_feedback"):
        config(min_pass_calibration_feedback_completeness_ratio=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_watch_stale_thesis"):
        config(min_watch_stale_thesis_label_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_item(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            input_item(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(input_item(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="specialist_label"):
        input_item(" raw-specialist")
    with pytest.raises(ValueError, match="specialist_label"):
        input_item("market_slug")
    with pytest.raises(ValueError, match="outcome_learning_note_count"):
        input_item(outcome_learning_note_count=d("0.000000"))
    with pytest.raises(ValueError, match="calibration_feedback_complete_count"):
        input_item(calibration_feedback_complete_count=9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_thesis_labeled_count"):
        input_item(stale_thesis_labeled_count=d("1.500000"))
    with pytest.raises(ValueError, match="error_taxonomy_tagged_count"):
        input_item(error_taxonomy_tagged_count=d("11.000000"))
    with pytest.raises(ValueError, match="high_priority_review_backlog_count"):
        input_item(
            open_review_backlog_count=d("1.000000"),
            high_priority_review_backlog_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        input_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_item(), paper_only=False)
    with pytest.raises(ValueError, match="writeback_readiness_score"):
        replace(populated.rows[0], writeback_readiness_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")


def test_owned_module_has_no_side_effect_imports_or_raw_public_surfaces() -> None:
    text = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lowered = text.lower()
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
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_text",
        "source_url",
    )

    assert all(term not in lowered for term in forbidden_terms)
    assert not any(
        isinstance(node, ast.Import | ast.ImportFrom)
        and any(alias.name.split(".")[0] in forbidden_terms for alias in node.names)
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"open", "print", "eval", "exec"}
        for node in ast.walk(tree)
    )


def is_numeric_public_field(field_name: str) -> bool:
    return field_name.endswith(
        (
            "_count",
            "_ratio",
            "_score",
            "_pressure",
        ),
    ) or field_name.startswith(("min_", "max_"))


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(walk_payload_keys(item))
    return tuple(keys)


def has_forbidden_public_surface_key(key: str) -> bool:
    return key in {
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_text",
        "source_url",
        "source_reference",
        "raw_text",
        "source_id",
    }
