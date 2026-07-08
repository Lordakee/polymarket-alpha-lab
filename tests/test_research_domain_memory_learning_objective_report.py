from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_domain_memory_learning_objective_report import (
    DEFAULT_RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_CONFIG_VERSION,
    RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_STATUSES,
    ResearchDomainMemoryLearningObjectiveConfig,
    ResearchDomainMemoryLearningObjectiveInputRow,
    ResearchDomainMemoryLearningObjectiveReasonCodeCount,
    ResearchDomainMemoryLearningObjectiveReport,
    ResearchDomainMemoryLearningObjectiveRow,
    build_research_domain_memory_learning_objective_report,
    research_domain_memory_learning_objective_report_digest,
    research_domain_memory_learning_objective_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_memory_learning_objective_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchDomainMemoryLearningObjectiveConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_CONFIG_VERSION
        ),
        "confidence_overreach_weight": d("0.250000"),
        "calibration_gap_weight": d("0.350000"),
        "evidence_gap_weight": d("0.250000"),
        "stale_memory_weight": d("0.150000"),
        "high_confidence_floor": d("0.700000"),
        "watch_calibration_error_ratio": d("0.150000"),
        "block_calibration_error_ratio": d("0.300000"),
        "watch_evidence_gap_count": d("2"),
        "block_evidence_gap_count": d("4"),
        "watch_stale_memory_ratio": d("0.300000"),
        "block_stale_memory_ratio": d("0.600000"),
        "min_memory_sample_count": d("3"),
        "watch_objective_score": d("0.250000"),
        "block_objective_score": d("0.600000"),
    }
    values.update(overrides)
    return ResearchDomainMemoryLearningObjectiveConfig(**values)


def input_row(
    domain: str = "macro",
    subdomain: str = "inflation",
    *,
    team_key: str = "team.macro.rates",
    past_confidence_score: Decimal = d("0.550000"),
    calibration_error_ratio: Decimal = d("0.050000"),
    evidence_gap_count: Decimal = d("0"),
    stale_memory_ratio: Decimal = d("0.100000"),
    memory_sample_count: Decimal = d("8"),
    last_memory_reviewed_at: datetime = GENERATED_AT - timedelta(days=3),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchDomainMemoryLearningObjectiveInputRow:
    return ResearchDomainMemoryLearningObjectiveInputRow(
        team_key=team_key,
        domain=domain,
        subdomain=subdomain,
        past_confidence_score=past_confidence_score,
        calibration_error_ratio=calibration_error_ratio,
        evidence_gap_count=evidence_gap_count,
        stale_memory_ratio=stale_memory_ratio,
        memory_sample_count=memory_sample_count,
        last_memory_reviewed_at=last_memory_reviewed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchDomainMemoryLearningObjectiveConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchDomainMemoryLearningObjectiveReport:
    return build_research_domain_memory_learning_objective_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for key, child in value.items():
            nested.append(key)
            nested.extend(walk_payload(child))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for child in value:
            nested.extend(walk_payload(child))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(public_record: object) -> None:
    for field in fields(public_record):
        if field.name in {
            "paper_only",
            "report_only",
            "readonly",
            "learning_objectives",
            "reason_codes",
            "derived_validation_digest",
        }:
            continue
        value = getattr(public_record, field.name)
        if isinstance(value, Decimal):
            assert type(value) is Decimal
            continue
        if (
            field.name.endswith(("_count", "_ratio", "_score"))
            or field.name.startswith(("average_", "max_"))
            or "confidence" in field.name
            or "calibration" in field.name
            or "stale" in field.name
            or "gap" in field.name
        ):
            assert type(value) is Decimal


def test_empty_report_blocks_with_public_safe_zero_payload() -> None:
    summary = report((), generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))))

    assert is_dataclass(summary)
    assert summary.__dataclass_params__.frozen
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_CONFIG_VERSION
    )
    assert RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert summary.objective_status == "block"
    assert summary.domain_count == d("0.000000")
    assert summary.subdomain_count == d("0.000000")
    assert summary.input_count == d("0.000000")
    assert summary.pass_count == d("0.000000")
    assert summary.watch_count == d("0.000000")
    assert summary.block_count == d("0.000000")
    assert summary.average_objective_score == d("0.000000")
    assert summary.max_objective_score == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == (
        "research_domain_memory_learning_objective_empty",
    )
    assert summary.reason_code_counts == (
        ResearchDomainMemoryLearningObjectiveReasonCodeCount(
            reason_code="research_domain_memory_learning_objective_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    payload = research_domain_memory_learning_objective_report_payload(summary)
    assert payload["domain_count"] == "0.000000"
    assert payload["derived_validation_digest"] == summary.derived_validation_digest
    json.dumps(payload, sort_keys=True)


def test_report_builds_domain_subdomain_objectives_from_memory_metrics() -> None:
    summary = report(
        (
            input_row(
                "macro",
                "inflation",
                team_key="team.macro.rates",
                past_confidence_score=d("0.900000"),
                calibration_error_ratio=d("0.350000"),
                evidence_gap_count=d("5"),
                stale_memory_ratio=d("0.700000"),
                memory_sample_count=d("2"),
            ),
            input_row(
                "weather",
                "hurricane",
                team_key="team.weather.energy",
                past_confidence_score=d("0.700000"),
                calibration_error_ratio=d("0.180000"),
                evidence_gap_count=d("2"),
                stale_memory_ratio=d("0.350000"),
                memory_sample_count=d("5"),
            ),
            input_row(
                "sports",
                "basketball",
                team_key="team.sports.nba",
                past_confidence_score=d("0.550000"),
                calibration_error_ratio=d("0.050000"),
                evidence_gap_count=d("0"),
                stale_memory_ratio=d("0.100000"),
                memory_sample_count=d("8"),
            ),
        ),
    )

    assert summary.objective_status == "block"
    assert summary.domain_count == d("3.000000")
    assert summary.subdomain_count == d("3.000000")
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_objective_score == d("0.383500")
    assert summary.max_objective_score == d("0.702500")
    assert summary.reason_codes == (
        "research_domain_memory_learning_objective_block_present",
        "research_domain_memory_learning_objective_watch_present",
        "research_domain_memory_learning_objective_confidence_overreach",
        "research_domain_memory_learning_objective_calibration_block",
        "research_domain_memory_learning_objective_calibration_watch",
        "research_domain_memory_learning_objective_evidence_gap_block",
        "research_domain_memory_learning_objective_evidence_gap_watch",
        "research_domain_memory_learning_objective_stale_memory_block",
        "research_domain_memory_learning_objective_stale_memory_watch",
        "research_domain_memory_learning_objective_thin_memory_sample",
    )

    assert tuple((row.objective_status, row.domain, row.subdomain) for row in summary.rows) == (
        ("block", "macro", "inflation"),
        ("watch", "weather", "hurricane"),
        ("pass", "sports", "basketball"),
    )

    blocked, watched, passed = summary.rows
    assert blocked.objective_score == d("0.702500")
    assert blocked.confidence_overreach_component == d("0.900000")
    assert blocked.evidence_gap_component == d("1.000000")
    assert blocked.learning_objectives == (
        "calibrate_confidence_to_resolved_outcomes",
        "close_public_evidence_gap_checklist",
        "refresh_stale_domain_memory",
        "expand_public_outcome_sample",
    )
    assert blocked.reason_codes == (
        "research_domain_memory_learning_objective_confidence_overreach",
        "research_domain_memory_learning_objective_calibration_block",
        "research_domain_memory_learning_objective_evidence_gap_block",
        "research_domain_memory_learning_objective_stale_memory_block",
        "research_domain_memory_learning_objective_thin_memory_sample",
    )

    assert watched.objective_score == d("0.415500")
    assert watched.learning_objectives == (
        "calibrate_confidence_to_resolved_outcomes",
        "close_public_evidence_gap_checklist",
        "refresh_stale_domain_memory",
    )
    assert watched.reason_codes == (
        "research_domain_memory_learning_objective_confidence_overreach",
        "research_domain_memory_learning_objective_calibration_watch",
        "research_domain_memory_learning_objective_evidence_gap_watch",
        "research_domain_memory_learning_objective_stale_memory_watch",
    )

    assert passed.objective_score == d("0.032500")
    assert passed.learning_objectives == ("maintain_current_learning_review_cadence",)
    assert passed.reason_codes == (
        "research_domain_memory_learning_objective_passed",
    )

    payload = research_domain_memory_learning_objective_report_payload(summary)
    assert payload["average_objective_score"] == "0.383500"
    assert payload["rows"][0]["objective_score"] == "0.702500"
    assert payload["rows"][0]["last_memory_reviewed_at"] == "2026-07-05T12:00:00+00:00"
    assert payload["rows"][0]["derived_validation_digest"] == (
        blocked.derived_validation_digest
    )
    assert payload["derived_validation_digest"] == summary.derived_validation_digest
    assert research_domain_memory_learning_objective_report_digest(summary) == (
        summary.derived_validation_digest
    )
    json.dumps(payload, sort_keys=True)

    unsafe_fragments = (
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "network",
        "database",
        "recommend",
    )
    for value in walk_payload(payload):
        if isinstance(value, str):
            lowered = value.lower()
            for fragment in unsafe_fragments:
                assert fragment not in lowered
        assert not isinstance(value, (Decimal, datetime, float))


def test_rows_reason_counts_payload_and_digest_are_deterministic() -> None:
    first = input_row(
        "macro",
        "inflation",
        team_key="team.macro.rates",
        past_confidence_score=d("0.900000"),
        calibration_error_ratio=d("0.350000"),
        evidence_gap_count=d("5"),
        stale_memory_ratio=d("0.700000"),
        memory_sample_count=d("2"),
    )
    second = input_row(
        "weather",
        "hurricane",
        team_key="team.weather.energy",
        past_confidence_score=d("0.700000"),
        calibration_error_ratio=d("0.180000"),
        evidence_gap_count=d("2"),
        stale_memory_ratio=d("0.350000"),
        memory_sample_count=d("5"),
    )
    third = input_row("sports", "basketball", team_key="team.sports.nba")

    forward = report((first, second, third))
    reverse = report((third, second, first))

    assert forward == reverse
    assert research_domain_memory_learning_objective_report_payload(forward) == (
        research_domain_memory_learning_objective_report_payload(reverse)
    )
    assert research_domain_memory_learning_objective_report_digest(forward) == (
        research_domain_memory_learning_objective_report_digest(reverse)
    )
    assert forward.reason_code_counts == tuple(
        sorted(
            forward.reason_code_counts,
            key=lambda item: forward.reason_codes.index(item.reason_code),
        ),
    )


def test_non_default_thresholds_can_downgrade_moderate_objective_to_pass() -> None:
    moderate = input_row(
        "weather",
        "hurricane",
        team_key="team.weather.energy",
        past_confidence_score=d("0.700000"),
        calibration_error_ratio=d("0.180000"),
        evidence_gap_count=d("2"),
        stale_memory_ratio=d("0.350000"),
        memory_sample_count=d("5"),
    )
    loose_config = config(
        watch_calibration_error_ratio=d("0.200000"),
        block_calibration_error_ratio=d("0.400000"),
        watch_evidence_gap_count=d("3"),
        block_evidence_gap_count=d("5"),
        watch_stale_memory_ratio=d("0.400000"),
        block_stale_memory_ratio=d("0.800000"),
        min_memory_sample_count=d("2"),
        watch_objective_score=d("0.500000"),
        block_objective_score=d("0.800000"),
    )

    summary = report((moderate,), cfg=loose_config)

    assert summary.objective_status == "pass"
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("0.000000")
    assert summary.block_count == d("0.000000")
    assert summary.rows[0].objective_status == "pass"
    assert summary.rows[0].reason_codes == (
        "research_domain_memory_learning_objective_passed",
    )
    assert summary.rows[0].learning_objectives == (
        "maintain_current_learning_review_cadence",
    )
    assert summary.reason_codes == (
        "research_domain_memory_learning_objective_clear",
    )


def test_validation_frozen_decimal_flags_duplicates_and_tamper_checks() -> None:
    good = input_row()
    summary = report((good,))

    with pytest.raises(FrozenInstanceError):
        good.domain = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.objective_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2")  # type: ignore[misc]

    for public_record in (
        config(),
        good,
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert_decimal_numeric_fields(public_record)

    with pytest.raises(TypeError, match="subclassing"):
        type("BadRow", (ResearchDomainMemoryLearningObjectiveRow,), {})
    with pytest.raises(ValueError, match="team_key must be a plain str"):
        input_row(team_key=_StringSubclass("team.macro.rates"))
    with pytest.raises(ValueError, match="past_confidence_score must be a Decimal"):
        input_row(past_confidence_score=_DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="calibration_error_ratio must be a Decimal"):
        input_row(calibration_error_ratio=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="last_memory_reviewed_at must be timezone-aware"):
        input_row(last_memory_reviewed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(
            (good,),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="last_memory_reviewed_at must be on or before generated_at"):
        report((input_row(last_memory_reviewed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="duplicate team/domain/subdomain"):
        report((input_row(), input_row()))
    with pytest.raises(ValueError, match="paper_only must be True"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        config(readonly=False)
    with pytest.raises(ValueError, match="confidence weights must sum to 1.000000"):
        config(confidence_overreach_weight=d("0.300000"))
    with pytest.raises(ValueError, match="watch_objective_score"):
        config(watch_objective_score=d("0.700000"), block_objective_score=d("0.600000"))
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(summary.rows[0], objective_score=d("0.900000"))
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(summary, generated_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="report must be"):
        research_domain_memory_learning_objective_report_payload(good)  # type: ignore[arg-type]


def test_module_has_no_durable_io_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: set[str] = set()
    call_names: set[str] = set()
    exported_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                call_names.add(func.id.lower())
            elif isinstance(func, ast.Attribute):
                call_names.add(func.attr.lower())
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    exported_names.update(
                        item.value
                        for item in node.value.elts
                        if isinstance(item, ast.Constant) and isinstance(item.value, str)
                    )

    assert not (imports & {"requests", "socket", "sqlite3", "sqlalchemy", "httpx", "urllib"})
    assert not (call_names & {"open", "put", "post", "patch", "delete", "send", "execute"})
    assert all("recommend" not in name.lower() for name in exported_names)
    assert "raw_market" not in MODULE_PATH.read_text(encoding="utf-8")
    assert "raw_source" not in MODULE_PATH.read_text(encoding="utf-8")
