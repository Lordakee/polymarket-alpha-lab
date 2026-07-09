from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_learning_retention_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_learning_retention_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def input_row(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "domain_team": "macro_policy",
        "learning_window": "weekly_resolution_review",
        "evaluated_at": GENERATED_AT - timedelta(hours=1),
        "calibration_carryforward_score": d("0.900000"),
        "correction_follow_through_score": d("0.880000"),
        "stale_memory_penalty_score": d("0.050000"),
        "evidence_reuse_quality_score": d("0.920000"),
        "peer_review_coverage_score": d("0.900000"),
        "review_latency_seconds": d("3600.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchTeamDomainLearningRetentionInputRow(**values)


def report(rows: tuple[Any, ...], **overrides: object):
    module = api()
    cfg = overrides.pop("config", None) or (
        module.ResearchTeamDomainLearningRetentionConfig()
    )
    return module.build_research_team_domain_learning_retention_report(
        rows,
        config=cfg,
        generated_at=overrides.pop("generated_at", GENERATED_AT),
    )


def report_values_with_matching_digest(
    module: Any,
    summary: Any,
    **overrides: object,
) -> dict[str, Any]:
    values = asdict(summary)
    values.update(overrides)
    values["derived_validation_digest"] = module._report_digest_from_mapping(values)
    return values


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_domain_learning_retention_scores_carryforward_followthrough_and_review_drag() -> None:
    module = api()

    summary = report(
        (
            input_row(
                domain_team="alpha_pass",
                learning_window="week_01",
                calibration_carryforward_score=d("0.900000"),
                correction_follow_through_score=d("0.880000"),
                stale_memory_penalty_score=d("0.050000"),
                evidence_reuse_quality_score=d("0.920000"),
                peer_review_coverage_score=d("0.900000"),
                review_latency_seconds=d("3600.000000"),
            ),
            input_row(
                domain_team="beta_watch",
                learning_window="week_01",
                calibration_carryforward_score=d("0.760000"),
                correction_follow_through_score=d("0.720000"),
                stale_memory_penalty_score=d("0.300000"),
                evidence_reuse_quality_score=d("0.740000"),
                peer_review_coverage_score=d("0.650000"),
                review_latency_seconds=d("10800.000000"),
            ),
            input_row(
                domain_team="gamma_block",
                learning_window="week_01",
                calibration_carryforward_score=d("0.520000"),
                correction_follow_through_score=d("0.400000"),
                stale_memory_penalty_score=d("0.520000"),
                evidence_reuse_quality_score=d("0.550000"),
                peer_review_coverage_score=d("0.300000"),
                review_latency_seconds=d("28800.000000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, module.ResearchTeamDomainLearningRetentionReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.report_status == "block"
    assert summary.learning_retention_gate_label == (
        "block_report_only_domain_learning_retention"
    )
    assert summary.domain_team_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_retention_score == d("0.673333")
    assert summary.average_calibration_carryforward_score == d("0.726667")
    assert summary.average_correction_follow_through_score == d("0.666667")
    assert summary.average_stale_memory_retention_score == d("0.710000")
    assert summary.average_evidence_reuse_quality_score == d("0.736667")
    assert summary.average_peer_review_coverage_score == d("0.616667")
    assert summary.average_review_latency_score == d("0.583333")
    assert summary.max_review_latency_seconds == d("28800.000000")
    assert summary.stale_memory_penalty_count == d("2.000000")
    assert summary.peer_review_gap_count == d("2.000000")
    assert summary.review_latency_gap_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.domain_team for row in summary.rows) == (
        "gamma_block",
        "beta_watch",
        "alpha_pass",
    )

    blocked, watched, passed = summary.rows
    assert blocked.public_status == "block"
    assert blocked.retention_score == d("0.375000")
    assert blocked.stale_memory_retention_score == d("0.480000")
    assert blocked.review_latency_score == d("0.000000")
    assert blocked.reason_codes == (
        "domain_learning_retention_block",
        "domain_learning_retention_calibration_carryforward_gap",
        "domain_learning_retention_correction_follow_through_gap",
        "domain_learning_retention_evidence_reuse_gap",
        "domain_learning_retention_peer_review_gap",
        "domain_learning_retention_review_latency_block",
        "domain_learning_retention_stale_memory_block",
    )

    assert watched.public_status == "watch"
    assert watched.retention_score == d("0.720000")
    assert watched.stale_memory_retention_score == d("0.700000")
    assert watched.review_latency_score == d("0.750000")
    assert watched.reason_codes == (
        "domain_learning_retention_calibration_carryforward_gap",
        "domain_learning_retention_correction_follow_through_gap",
        "domain_learning_retention_evidence_reuse_gap",
        "domain_learning_retention_peer_review_gap",
        "domain_learning_retention_review_latency_gap",
        "domain_learning_retention_stale_memory_watch",
        "domain_learning_retention_watch",
    )

    assert passed.public_status == "pass"
    assert passed.retention_score == d("0.925000")
    assert passed.stale_memory_retention_score == d("0.950000")
    assert passed.review_latency_score == d("1.000000")
    assert passed.reason_codes == ("domain_learning_retention_pass",)

    reason_counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert reason_counts["domain_learning_retention_calibration_carryforward_gap"].count == (
        d("2.000000")
    )
    assert reason_counts["domain_learning_retention_calibration_carryforward_gap"].team_ratio == (
        d("0.666667")
    )
    assert reason_counts["domain_learning_retention_pass"].count == d("1.000000")
    assert summary.reason_codes == tuple(row.reason_code for row in summary.reason_code_counts)


def test_empty_inputs_return_block_report_only_digest() -> None:
    module = api()
    summary = report(())

    assert summary.report_status == "block"
    assert summary.domain_team_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("domain_learning_retention_no_inputs",)
    assert summary.reason_code_counts == (
        module.ResearchTeamDomainLearningRetentionReasonCodeCount(
            reason_code="domain_learning_retention_no_inputs",
            count=d("1.000000"),
            team_ratio=d("0.000000"),
        ),
    )
    assert summary.derived_validation_digest == (
        module.research_team_domain_learning_retention_report_digest(summary)
    )


def test_payload_is_deterministic_public_decimal_only_and_digest_validated() -> None:
    module = api()
    first = report(
        (
            input_row(domain_team="zeta_watch", stale_memory_penalty_score=d("0.300000")),
            input_row(domain_team="alpha_pass"),
        ),
    )
    second = report(
        (
            input_row(domain_team="alpha_pass"),
            input_row(domain_team="zeta_watch", stale_memory_penalty_score=d("0.300000")),
        ),
    )

    first_payload = module.research_team_domain_learning_retention_report_payload(first)
    second_payload = module.research_team_domain_learning_retention_report_payload(second)
    first_digest = module.research_team_domain_learning_retention_report_digest(first)

    assert first_payload == second_payload
    assert first_digest == (
        module.research_team_domain_learning_retention_report_digest(second)
    )
    assert first.payload == first_payload
    assert first.derived_validation_digest == first_digest
    assert len(first_digest) == 64
    assert first_payload["derived_validation_digest"] == first_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["rows"][0]["public_status"] == "watch"
    assert first_payload["rows"][0]["retention_score"] == "0.883333"

    public = repr(first_payload).lower()
    for token in (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "http",
        "source_text",
        "source_id",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert token not in public
    assert_no_float_values(first_payload)

    tampered = asdict(first)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchTeamDomainLearningRetentionReport(**tampered)


def test_matching_digest_reports_still_validate_public_schema() -> None:
    module = api()
    summary = report((input_row(),))

    inconsistent_status_counts = report_values_with_matching_digest(
        module,
        summary,
        pass_count=d("0.000000"),
        watch_count=d("1.000000"),
    )
    with pytest.raises(ValueError, match="pass_count"):
        module.ResearchTeamDomainLearningRetentionReport(**inconsistent_status_counts)

    inconsistent_average = report_values_with_matching_digest(
        module,
        summary,
        average_retention_score=d("0.000000"),
    )
    with pytest.raises(ValueError, match="average_retention_score"):
        module.ResearchTeamDomainLearningRetentionReport(**inconsistent_average)

    inconsistent_reason_counts = report_values_with_matching_digest(
        module,
        summary,
        reason_code_counts=(
            module.ResearchTeamDomainLearningRetentionReasonCodeCount(
                reason_code="domain_learning_retention_pass",
                count=d("2.000000"),
                team_ratio=d("1.000000"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.ResearchTeamDomainLearningRetentionReport(**inconsistent_reason_counts)


def test_report_rows_validate_public_status_reason_and_score_schema() -> None:
    module = api()
    row_values = asdict(report((input_row(),)).rows[0])

    mismatched_reason_codes = {
        **row_values,
        "reason_codes": ("domain_learning_retention_watch",),
    }
    with pytest.raises(ValueError, match="reason_codes"):
        module.ResearchTeamDomainLearningRetentionReportRow(**mismatched_reason_codes)

    drifted_retention_score = {
        **row_values,
        "retention_score": d("0.000000"),
    }
    with pytest.raises(ValueError, match="retention_score"):
        module.ResearchTeamDomainLearningRetentionReportRow(**drifted_retention_score)


def test_validates_types_statuses_flags_and_freezing() -> None:
    module = api()

    for cls_name in (
        "ResearchTeamDomainLearningRetentionConfig",
        "ResearchTeamDomainLearningRetentionInputRow",
        "ResearchTeamDomainLearningRetentionReasonCodeCount",
        "ResearchTeamDomainLearningRetentionReport",
        "ResearchTeamDomainLearningRetentionReportRow",
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Unsafe{cls_name}", (getattr(module, cls_name),), {})

    with pytest.raises(TypeError, match="Decimal"):
        input_row(calibration_carryforward_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="datetime"):
        report((input_row(),), generated_at="2026-07-08T18:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        report((input_row(),), generated_at=datetime(2026, 7, 8, 18, 0))

    with pytest.raises(ValueError, match="whole second"):
        report((input_row(),), generated_at=datetime(2026, 7, 8, 18, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(TypeError, match="exactly"):
        input_row(domain_team=_StringSubclass("macro_policy"))

    with pytest.raises(ValueError, match="public"):
        input_row(domain_team="ｍａｒｋｅｔ")

    with pytest.raises(TypeError, match="exactly"):
        input_row(evidence_reuse_quality_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="unit interval"):
        input_row(peer_review_coverage_score=d("1.000001"))

    with pytest.raises(ValueError, match="nonnegative"):
        input_row(review_latency_seconds=d("-1.000000"))

    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)

    with pytest.raises(TypeError, match="Decimal"):
        module.ResearchTeamDomainLearningRetentionConfig(
            pass_retention_score=1,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="whole Decimal"):
        module.ResearchTeamDomainLearningRetentionReasonCodeCount(
            reason_code=module.PASS_REASON,
            count=d("1.500000"),
            team_ratio=d("1.000000"),
        )

    summary_row_values = asdict(report((input_row(),)).rows[0])
    summary_row_values["public_status"] = _StringSubclass("pass")
    with pytest.raises(TypeError, match="exactly str"):
        module.ResearchTeamDomainLearningRetentionReportRow(**summary_row_values)

    mutated_config = module.ResearchTeamDomainLearningRetentionConfig()
    object.__setattr__(mutated_config, "pass_retention_score", d("2.000000"))
    with pytest.raises(ValueError, match="unit interval"):
        report((input_row(),), config=mutated_config)

    frozen = input_row()
    with pytest.raises(FrozenInstanceError):
        frozen.calibration_carryforward_score = d("0.100000")  # type: ignore[misc]

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.report_status = "pass"  # type: ignore[misc]

    assert replace(frozen, calibration_carryforward_score=d("0.880000")).calibration_carryforward_score == (
        d("0.880000")
    )
    assert {summary.report_status, *(row.public_status for row in summary.rows)} <= {
        "pass",
        "watch",
        "block",
    }
    for obj in (summary, *summary.rows, *summary.reason_code_counts):
        for field in fields(obj):
            if field.name.endswith("status"):
                assert getattr(obj, field.name) in {"pass", "watch", "block"}


def test_public_inputs_reject_private_or_actionable_surfaces() -> None:
    leak_values = (
        _join_parts("raw_", "candidate", "_17"),
        _join_parts("market", "_ref"),
        _join_parts("market", "_slug"),
        _join_parts("market", "-", "id"),
        _join_parts("market", ".", "slug"),
        _join_parts("market", "id"),
        _join_parts("will", "_team", "_win", "_question"),
        _join_parts("source", "_ref"),
        _join_parts("url", "_path"),
        _join_parts("resolution", "_text"),
        _join_parts("source", "_text"),
        _join_parts("source", ".", "text"),
        _join_parts("auth", "_surface"),
        _join_parts("api", "_key"),
        _join_parts("credential", "_surface"),
        _join_parts("password", "_surface"),
        _join_parts("secret", "_surface"),
        _join_parts("session", "_cookie"),
        _join_parts("database", "_surface"),
        _join_parts("dsn", "_analytics"),
        _join_parts("postgres", "_surface"),
        _join_parts("supabase", "_surface"),
        _join_parts("sql", "_query"),
        _join_parts("network", "_surface"),
        _join_parts("endpoint", "_surface"),
        _join_parts("socket", "_surface"),
        _join_parts("table", "_name"),
        _join_parts("file", "_path"),
        _join_parts("sizing", "_surface"),
        _join_parts("recommendation", "_surface"),
        _join_parts("to", "ken", "_abc"),
        _join_parts("to", "-", "ken", "_abc"),
        _join_parts("wal", "let", "_field"),
        _join_parts("sub", "mit", "_order"),
        _join_parts("or", ".", "der", "_surface"),
        _join_parts("trading", "_surface"),
        _join_parts("trade", "_surface"),
        _join_parts("tr", "-", "ade", "_surface"),
        _join_parts("execution", "_surface"),
        _join_parts("live", "_surface"),
    )

    for value in leak_values:
        with pytest.raises(ValueError, match="public"):
            input_row(domain_team=value)


def test_payload_and_digest_revalidate_frozen_report_state() -> None:
    module = api()

    summary = report((input_row(),))
    object.__setattr__(summary, "average_retention_score", d("0.000000"))
    for public_function in (
        module.research_team_domain_learning_retention_report_payload,
        module.research_team_domain_learning_retention_report_digest,
    ):
        with pytest.raises(ValueError, match="average_retention_score"):
            public_function(summary)

    row_tampered = report((input_row(),))
    object.__setattr__(
        row_tampered.rows[0],
        "stale_memory_penalty_score",
        d("0.100000"),
    )
    object.__setattr__(
        row_tampered,
        "derived_validation_digest",
        module._report_digest_from_payload(row_tampered, include_digest=False),
    )
    for public_function in (
        module.research_team_domain_learning_retention_report_payload,
        module.research_team_domain_learning_retention_report_digest,
    ):
        with pytest.raises(ValueError, match="stale_memory_retention_score"):
            public_function(row_tampered)

    flag_tampered = report((input_row(),))
    object.__setattr__(flag_tampered, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_domain_learning_retention_report_digest(flag_tampered)


def test_module_is_pure_report_only_and_has_no_io_or_action_surface() -> None:
    module = api()
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(module_source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "delete",
        "cursor",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)

    for cls_name in (
        "ResearchTeamDomainLearningRetentionConfig",
        "ResearchTeamDomainLearningRetentionInputRow",
        "ResearchTeamDomainLearningRetentionReasonCodeCount",
        "ResearchTeamDomainLearningRetentionReport",
        "ResearchTeamDomainLearningRetentionReportRow",
    ):
        cls = getattr(module, cls_name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
