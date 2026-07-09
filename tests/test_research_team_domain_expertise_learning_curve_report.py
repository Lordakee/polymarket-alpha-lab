from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_team_domain_expertise_learning_curve_report as api
from polymarket_alpha_lab.research_team_domain_expertise_learning_curve_report import (
    DEFAULT_RESEARCH_TEAM_DOMAIN_EXPERTISE_LEARNING_CURVE_CONFIG_VERSION,
    ResearchTeamDomainExpertiseLearningCurveConfig,
    ResearchTeamDomainExpertiseLearningCurveInput,
    ResearchTeamDomainExpertiseLearningCurveReasonCodeCount,
    ResearchTeamDomainExpertiseLearningCurveReport,
    ResearchTeamDomainExpertiseLearningCurveRow,
    build_research_team_domain_expertise_learning_curve_report,
    research_team_domain_expertise_learning_curve_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def item(
    team_key: str = "macro_team",
    *,
    domain_key: str = "rates",
    learning_label: str = "policy_path",
    observed_at: datetime = GENERATED_AT,
    forecast_outcome_count: Decimal = d("12.000000"),
    useful_outcome_count: Decimal = d("10.000000"),
    evidence_quality_score: Decimal = d("0.860000"),
    correction_latency_seconds: Decimal = d("43200.000000"),
    calibration_error_before: Decimal = d("0.160000"),
    calibration_error_after: Decimal = d("0.070000"),
    playbook_adoption_rate: Decimal = d("0.800000"),
    private_learning_note: str = "Base-rate bins improved after settlement review.",
    trace_marker: str = "",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamDomainExpertiseLearningCurveInput:
    return ResearchTeamDomainExpertiseLearningCurveInput(
        team_key=team_key,
        domain_key=domain_key,
        learning_label=learning_label,
        observed_at=observed_at,
        forecast_outcome_count=forecast_outcome_count,
        useful_outcome_count=useful_outcome_count,
        evidence_quality_score=evidence_quality_score,
        correction_latency_seconds=correction_latency_seconds,
        calibration_error_before=calibration_error_before,
        calibration_error_after=calibration_error_after,
        playbook_adoption_rate=playbook_adoption_rate,
        private_learning_note=private_learning_note,
        trace_marker=trace_marker,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchTeamDomainExpertiseLearningCurveInput, ...],
    *,
    cfg: ResearchTeamDomainExpertiseLearningCurveConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamDomainExpertiseLearningCurveReport:
    return build_research_team_domain_expertise_learning_curve_report(
        rows,
        config=cfg or ResearchTeamDomainExpertiseLearningCurveConfig(),
        generated_at=generated_at,
    )


def test_domain_expertise_report_scores_pass_watch_and_block_learning_curves() -> None:
    summary = report(
        (
            item(
                "gamma_team",
                domain_key="sports",
                learning_label="injury_revision",
                forecast_outcome_count=d("1.000000"),
                useful_outcome_count=d("0.000000"),
                evidence_quality_score=d("0.300000"),
                correction_latency_seconds=d("1209600.000000"),
                calibration_error_before=d("0.100000"),
                calibration_error_after=d("0.220000"),
                playbook_adoption_rate=d("0.200000"),
            ),
            item("alpha_team", domain_key="rates", learning_label="policy_path"),
            item(
                "beta_team",
                domain_key="crypto",
                learning_label="flow_revision",
                forecast_outcome_count=d("4.000000"),
                useful_outcome_count=d("2.000000"),
                evidence_quality_score=d("0.620000"),
                correction_latency_seconds=d("259200.000000"),
                calibration_error_before=d("0.180000"),
                calibration_error_after=d("0.170000"),
                playbook_adoption_rate=d("0.550000"),
            ),
        ),
    )

    assert isinstance(summary, ResearchTeamDomainExpertiseLearningCurveReport)
    assert is_dataclass(summary)
    assert summary.config_version == (
        DEFAULT_RESEARCH_TEAM_DOMAIN_EXPERTISE_LEARNING_CURVE_CONFIG_VERSION
    )
    assert summary.report_status == "block"
    assert summary.next_step == "block_domain_expertise_learning_curve_report"
    assert summary.domain_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.forecast_outcome_count == d("17.000000")
    assert summary.useful_outcome_count == d("12.000000")
    assert summary.outcome_usefulness_ratio == d("0.705882")
    assert summary.average_evidence_quality_score == d("0.593333")
    assert summary.average_correction_latency_score == d("0.500000")
    assert summary.average_calibration_movement_score == d("0.400000")
    assert summary.average_playbook_adoption_rate == d("0.516667")
    assert summary.average_expertise_learning_score == d("0.471111")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.team_key for row in summary.rows) == (
        "alpha_team",
        "beta_team",
        "gamma_team",
    )
    pass_row, watch_row, block_row = summary.rows
    assert pass_row.expertise_learning_score == d("0.882619")
    assert pass_row.expertise_status == "pass"
    assert pass_row.reason_codes == (
        "domain_expertise_learning_curve_calibration_movement_pass",
        "domain_expertise_learning_curve_correction_latency_pass",
        "domain_expertise_learning_curve_evidence_quality_pass",
        "domain_expertise_learning_curve_forecast_outcomes_pass",
        "domain_expertise_learning_curve_pass",
        "domain_expertise_learning_curve_playbook_adoption_pass",
    )
    assert watch_row.expertise_learning_score == d("0.425714")
    assert watch_row.expertise_status == "watch"
    assert "domain_expertise_learning_curve_forecast_outcomes_watch" in (
        watch_row.reason_codes
    )
    assert "domain_expertise_learning_curve_calibration_movement_watch" in (
        watch_row.reason_codes
    )
    assert block_row.expertise_learning_score == d("0.105000")
    assert block_row.expertise_status == "block"
    assert "domain_expertise_learning_curve_calibration_regression_block" in (
        block_row.reason_codes
    )
    assert "domain_expertise_learning_curve_playbook_adoption_block" in (
        block_row.reason_codes
    )
    assert {row.expertise_status for row in summary.rows} == {"pass", "watch", "block"}


def test_payload_is_deterministic_decimal_stringified_and_digest_validated() -> None:
    raw_private_note = (
        "raw candidate id CAND-7 market id MKT-9 market slug fed-rates "
        "market question Will it happen source url https://example.test/private "
        "source text says buy sell wallet order trade dsn table token live"
    )
    rows = (
        item(
            "beta_team",
            domain_key="crypto",
            learning_label="flow_revision",
            forecast_outcome_count=d("4.000000"),
            useful_outcome_count=d("2.000000"),
            evidence_quality_score=d("0.620000"),
            correction_latency_seconds=d("259200.000000"),
            calibration_error_before=d("0.180000"),
            calibration_error_after=d("0.170000"),
            playbook_adoption_rate=d("0.550000"),
            private_learning_note=raw_private_note,
            trace_marker="wallet=0x1111111111111111111111111111111111111111",
        ),
        item("alpha_team", domain_key="rates", learning_label="policy_path"),
    )
    first = report(rows)
    second = report(tuple(reversed(rows)))

    first_payload = research_team_domain_expertise_learning_curve_report_payload(first)
    second_payload = research_team_domain_expertise_learning_curve_report_payload(second)
    json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["domain_count"] == "2.000000"
    assert first_payload["average_expertise_learning_score"] == "0.654167"
    assert first_payload["rows"][0]["expertise_learning_score"] == "0.882619"
    assert first_payload["rows"][1]["expertise_learning_score"] == "0.425714"
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first_payload["derived_validation_digest"]) == 64
    assert first.derived_validation_digest == second.derived_validation_digest
    assert _contains_no_decimal_or_float(first_payload)

    public = repr(first_payload).lower()
    for token in (
        "cand-7",
        "mkt-9",
        "fed-rates",
        "will it happen",
        "example.test",
        "private",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "dsn",
        "table",
        "token",
        "live",
    ):
        assert token not in public


def test_validation_rejects_non_decimal_types_unsafe_surfaces_and_mutation() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        item(forecast_outcome_count=1)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Decimal"):
        item(evidence_quality_score=_DecimalSubclass("0.900000"))

    with pytest.raises(TypeError, match="datetime"):
        item(observed_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))

    with pytest.raises(TypeError, match="str"):
        item(team_key=_StringSubclass("alpha_team"))

    with pytest.raises(ValueError, match="UTC-aware"):
        item(observed_at=datetime(2026, 7, 8, 12, 0))

    with pytest.raises(ValueError, match="whole count"):
        item(forecast_outcome_count=d("1.500000"))

    with pytest.raises(ValueError, match="useful_outcome_count"):
        item(forecast_outcome_count=d("1.000000"), useful_outcome_count=d("2.000000"))

    with pytest.raises(ValueError, match="unit interval"):
        item(playbook_adoption_rate=d("1.000001"))

    with pytest.raises(ValueError, match="unsafe"):
        item(domain_key="market_slug")

    with pytest.raises(ValueError, match="unsafe"):
        item(learning_label="candidate_question")

    with pytest.raises(ValueError, match="paper_only"):
        item(paper_only=False)

    frozen = item()
    with pytest.raises(FrozenInstanceError):
        frozen.evidence_quality_score = d("0.100000")  # type: ignore[misc]

    summary = report((item(),))
    with pytest.raises(FrozenInstanceError):
        summary.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(ResearchTeamDomainExpertiseLearningCurveReport):
            pass


def test_report_payload_and_digest_consistency_are_enforced() -> None:
    summary = report(
        (
            item("alpha_team", domain_key="rates", learning_label="policy_path"),
            item(
                "beta_team",
                domain_key="crypto",
                learning_label="flow_revision",
                forecast_outcome_count=d("4.000000"),
                useful_outcome_count=d("2.000000"),
                evidence_quality_score=d("0.620000"),
                correction_latency_seconds=d("259200.000000"),
                calibration_error_before=d("0.180000"),
                calibration_error_after=d("0.170000"),
                playbook_adoption_rate=d("0.550000"),
            ),
        ),
    )
    payload = research_team_domain_expertise_learning_curve_report_payload(summary)

    assert summary.report_status == "watch"
    assert payload["report_status"] == summary.report_status
    assert payload["reason_codes"] == [
        count.reason_code for count in summary.reason_code_counts
    ]

    with pytest.raises(ValueError, match="domain_count"):
        replace(summary, domain_count=d("99.000000"))

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            rows=(
                replace(summary.rows[0], playbook_adoption_rate=d("0.700000")),
                summary.rows[1],
            ),
        )

    with pytest.raises(TypeError, match="report"):
        research_team_domain_expertise_learning_curve_report_payload(object())  # type: ignore[arg-type]

    empty = report(())
    assert empty.report_status == "block"
    assert empty.rows == ()
    assert empty.reason_code_counts == (
        ResearchTeamDomainExpertiseLearningCurveReasonCodeCount(
            reason_code="domain_expertise_learning_curve_no_inputs",
            count=d("1.000000"),
            domain_ratio=d("0.000000"),
        ),
    )


def test_payload_property_enforces_public_flags_digest_and_schema() -> None:
    summary = report((item(),))
    payload = summary.payload

    assert set(payload) == {field.name for field in fields(summary)}
    assert set(payload["rows"][0]) == {field.name for field in fields(summary.rows[0])}
    assert set(payload["reason_code_counts"][0]) == {
        field.name for field in fields(summary.reason_code_counts[0])
    }

    object.__setattr__(summary, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        summary.payload

    object.__setattr__(summary, "paper_only", True)
    object.__setattr__(summary, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        summary.payload


def test_module_is_report_only_with_no_runtime_io_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_domain_expertise_learning_curve_report.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

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
        "cursor",
        "delete",
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

    for cls in (
        ResearchTeamDomainExpertiseLearningCurveConfig,
        ResearchTeamDomainExpertiseLearningCurveInput,
        ResearchTeamDomainExpertiseLearningCurveRow,
        ResearchTeamDomainExpertiseLearningCurveReasonCodeCount,
        ResearchTeamDomainExpertiseLearningCurveReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        for field in fields(cls):
            assert field.name not in {"candidate_id", "market_id", "slug", "question"}

    for public_name in api.__all__:
        assert "candidate" not in public_name.lower()
        assert "market" not in public_name.lower()


def _contains_no_decimal_or_float(value: object) -> bool:
    if isinstance(value, (Decimal, float)):
        return False
    if isinstance(value, dict):
        return all(_contains_no_decimal_or_float(item) for item in value.values())
    if isinstance(value, list):
        return all(_contains_no_decimal_or_float(item) for item in value)
    return True
