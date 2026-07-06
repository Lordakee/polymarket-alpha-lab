from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_candidate_event_specificity_score_v10 import (
    StrategyCandidateEventSpecificityScoreV10Input,
    StrategyCandidateEventSpecificityScoreV10Report,
    build_strategy_candidate_event_specificity_score_v10_report,
    strategy_candidate_event_specificity_score_v10_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/strategy_candidate_event_specificity_score_v10.py",
)


class StrategyCandidateEventSpecificityScoreV10InputSubclass(
    StrategyCandidateEventSpecificityScoreV10Input,
):
    pass


class StrategyCandidateEventSpecificityScoreV10ReportSubclass(
    StrategyCandidateEventSpecificityScoreV10Report,
):
    pass


def _report(
    *,
    candidate_id: str = "candidate-1",
    ambiguous_term_count: Decimal = Decimal("0"),
    measurable_resolution_criteria_score: Decimal = Decimal("1"),
    source_alignment_score: Decimal = Decimal("1"),
    deadline_clarity_score: Decimal = Decimal("1"),
    adjudication_complexity_score: Decimal = Decimal("0"),
) -> StrategyCandidateEventSpecificityScoreV10Report:
    return build_strategy_candidate_event_specificity_score_v10_report(
        candidate_id=candidate_id,
        ambiguous_term_count=ambiguous_term_count,
        measurable_resolution_criteria_score=measurable_resolution_criteria_score,
        source_alignment_score=source_alignment_score,
        deadline_clarity_score=deadline_clarity_score,
        adjudication_complexity_score=adjudication_complexity_score,
    )


def test_specificity_score_passes_for_clear_measurable_aligned_event() -> None:
    report = _report()

    assert report.candidate_id == "candidate-1"
    assert report.specificity_status == "pass"
    assert report.specificity_risk_score == Decimal("0.000000")
    assert report.required_followups == ()
    assert report.reason_codes == ("specificity_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    for value in (
        report.ambiguous_term_count,
        report.measurable_resolution_criteria_score,
        report.source_alignment_score,
        report.deadline_clarity_score,
        report.adjudication_complexity_score,
        report.specificity_risk_score,
    ):
        assert type(value) is Decimal


def test_specificity_score_watches_moderately_ambiguous_event_contract() -> None:
    report = _report(
        candidate_id="candidate-watch",
        ambiguous_term_count=Decimal("2"),
        measurable_resolution_criteria_score=Decimal("0.70"),
        source_alignment_score=Decimal("0.80"),
        deadline_clarity_score=Decimal("0.60"),
        adjudication_complexity_score=Decimal("0.40"),
    )

    assert report.specificity_status == "watch"
    assert report.specificity_risk_score == Decimal("0.345000")
    assert report.required_followups == (
        "rewrite_ambiguous_market_terms",
        "add_measurable_resolution_criteria",
        "clarify_resolution_deadline",
    )
    assert report.reason_codes == (
        "ambiguous_terms_present",
        "measurable_resolution_criteria_gap",
        "deadline_clarity_gap",
        "adjudication_complexity_present",
    )


def test_specificity_score_blocks_source_conflict_and_complex_adjudication() -> None:
    report = _report(
        candidate_id="candidate-blocked",
        ambiguous_term_count=Decimal("5"),
        measurable_resolution_criteria_score=Decimal("0.20"),
        source_alignment_score=Decimal("0.20"),
        deadline_clarity_score=Decimal("0.10"),
        adjudication_complexity_score=Decimal("0.90"),
    )

    assert report.specificity_status == "blocked"
    assert report.specificity_risk_score == Decimal("1.000000")
    assert report.required_followups == (
        "rewrite_ambiguous_market_terms",
        "add_measurable_resolution_criteria",
        "verify_resolution_source_alignment",
        "clarify_resolution_deadline",
        "reduce_adjudication_complexity",
    )
    assert report.reason_codes == (
        "ambiguous_terms_high",
        "measurable_resolution_criteria_gap",
        "source_alignment_conflict",
        "deadline_clarity_gap",
        "adjudication_complexity_high",
    )


def test_specificity_score_payload_is_report_only_and_preserves_decimals() -> None:
    report = _report(
        candidate_id="candidate-payload",
        ambiguous_term_count=Decimal("2"),
        measurable_resolution_criteria_score=Decimal("0.70"),
        source_alignment_score=Decimal("0.80"),
        deadline_clarity_score=Decimal("0.60"),
        adjudication_complexity_score=Decimal("0.40"),
    )

    payload = strategy_candidate_event_specificity_score_v10_payload(report)

    assert payload == report.payload
    assert payload == {
        "candidate_id": "candidate-payload",
        "ambiguous_term_count": Decimal("2"),
        "measurable_resolution_criteria_score": Decimal("0.70"),
        "source_alignment_score": Decimal("0.80"),
        "deadline_clarity_score": Decimal("0.60"),
        "adjudication_complexity_score": Decimal("0.40"),
        "specificity_status": "watch",
        "specificity_risk_score": Decimal("0.345000"),
        "required_followups": [
            "rewrite_ambiguous_market_terms",
            "add_measurable_resolution_criteria",
            "clarify_resolution_deadline",
        ],
        "reason_codes": [
            "ambiguous_terms_present",
            "measurable_resolution_criteria_gap",
            "deadline_clarity_gap",
            "adjudication_complexity_present",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("candidate_id", "", "candidate_id"),
        ("candidate_id", " candidate-1 ", "candidate_id"),
        ("ambiguous_term_count", 1, "ambiguous_term_count"),
        ("ambiguous_term_count", Decimal("-1"), "ambiguous_term_count"),
        ("ambiguous_term_count", Decimal("1.5"), "ambiguous_term_count"),
        (
            "measurable_resolution_criteria_score",
            Decimal("1.01"),
            "measurable_resolution_criteria_score",
        ),
        ("source_alignment_score", Decimal("-0.01"), "source_alignment_score"),
        ("deadline_clarity_score", Decimal("NaN"), "deadline_clarity_score"),
        ("adjudication_complexity_score", Decimal("1.01"), "adjudication_complexity_score"),
        ("paper_only", False, "paper_only"),
        ("report_only", False, "report_only"),
        ("readonly", False, "readonly"),
    ),
)
def test_specificity_score_input_validates_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    kwargs: dict[str, object] = {
        "candidate_id": "candidate-1",
        "ambiguous_term_count": Decimal("0"),
        "measurable_resolution_criteria_score": Decimal("1"),
        "source_alignment_score": Decimal("1"),
        "deadline_clarity_score": Decimal("1"),
        "adjudication_complexity_score": Decimal("0"),
        field_name: bad_value,
    }

    with pytest.raises(ValueError, match=message):
        StrategyCandidateEventSpecificityScoreV10Input(**kwargs)


def test_specificity_score_outputs_are_frozen_and_consistent() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.specificity_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="specificity_status"):
        replace(report, specificity_status="blocked")
    with pytest.raises(ValueError, match="specificity_risk_score"):
        replace(report, specificity_risk_score=Decimal("0.500000"))
    with pytest.raises(ValueError, match="required_followups"):
        replace(report, required_followups=("rewrite_ambiguous_market_terms",))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=["specificity_clear"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_specificity_score_rejects_subclasses() -> None:
    input_row = StrategyCandidateEventSpecificityScoreV10Input(
        candidate_id="candidate-1",
        ambiguous_term_count=Decimal("0"),
        measurable_resolution_criteria_score=Decimal("1"),
        source_alignment_score=Decimal("1"),
        deadline_clarity_score=Decimal("1"),
        adjudication_complexity_score=Decimal("0"),
    )
    report = _report()

    with pytest.raises(ValueError, match="input"):
        StrategyCandidateEventSpecificityScoreV10InputSubclass(**input_row.__dict__)
    with pytest.raises(ValueError, match="report"):
        StrategyCandidateEventSpecificityScoreV10ReportSubclass(**report.__dict__)


def test_specificity_score_module_scope_stays_pure_readonly() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {
                    "float",
                    "open",
                    "print",
                    "recommend",
                    "submit",
                    "sign",
                }
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "execute",
                    "fetch",
                    "read",
                    "request",
                    "submit",
                    "write",
                }

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "typing",
    }

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    for banned_term in (
        "psycopg",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "websocket",
        "websockets",
        "eth_account",
        "private_key",
        "wallet",
        "auth",
        "clob",
        "gamma",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "order",
    ):
        assert banned_term not in source
