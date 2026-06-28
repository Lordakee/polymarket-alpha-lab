from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest


GENERATED_AT = datetime(2026, 6, 27, 12, 0, tzinfo=UTC)
SELECTION_AT = datetime(2026, 6, 27, 11, 55, tzinfo=UTC)
SCORER_AT = datetime(2026, 6, 27, 11, 58, tzinfo=UTC)


def _module():
    from polymarket_alpha_lab import probability_selection_scorer_agreement

    return probability_selection_scorer_agreement


def _selection_report(
    rows: tuple[SimpleNamespace, ...] = (),
    *,
    selected_rows: tuple[SimpleNamespace, ...] | None = None,
    generated_at: datetime = SELECTION_AT,
) -> SimpleNamespace:
    kwargs: dict[str, object] = {
        "generated_at": generated_at,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if selected_rows is None:
        kwargs["rows"] = rows
    else:
        kwargs["selected_rows"] = selected_rows
    return SimpleNamespace(**kwargs)


def _scorer_report(
    candidates: tuple[SimpleNamespace, ...] = (),
    *,
    candidate_attr: str = "candidates",
    gate_status: str = "pass",
    generated_at: datetime = SCORER_AT,
) -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=generated_at,
        gate_status=gate_status,
        **{candidate_attr: candidates},
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _selection_row(
    market_slug: str | None,
    condition_id: str | None,
    *,
    status: str = "ready",
    action: str = "recommend",
    recommendation: str = "select",
    reason_codes: tuple[str, ...] = ("shared_reason",),
) -> SimpleNamespace:
    return SimpleNamespace(
        market_slug=market_slug,
        condition_id=condition_id,
        status=status,
        action=action,
        recommendation=recommendation,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _scorer_candidate(
    market_slug: str | None,
    condition_id: str | None,
    *,
    status: str = "scored",
    reason_codes: tuple[str, ...] = ("shared_reason",),
) -> SimpleNamespace:
    return SimpleNamespace(
        market_slug=market_slug,
        condition_id=condition_id,
        score_status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_agreement_audit_reports_aligned_selection_scorer_overlap() -> None:
    agreement = _module()
    selection = _selection_report(
        selected_rows=(
            _selection_row("alpha", "cond-alpha"),
            _selection_row("beta", "cond-beta"),
        ),
    )
    scorer = _scorer_report(
        (
            _scorer_candidate("alpha", "cond-alpha"),
            _scorer_candidate("beta", "cond-beta"),
        ),
        candidate_attr="candidate_rows",
    )

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "probability-selection-scorer-agreement-v0"
    assert report.selection_generated_at == SELECTION_AT
    assert report.scorer_generated_at == SCORER_AT
    assert report.selected_count == 2
    assert report.scorer_candidate_count == 2
    assert report.selected_market_overlap_count == 2
    assert report.selected_condition_overlap_count == 2
    assert report.rejected_but_scored_count == 0
    assert report.scored_but_unselected_count == 0
    assert report.scorer_gate_status == "pass"
    assert report.agreement_status == "aligned"
    assert report.recommended_next_step == "continue_monitoring"
    assert report.reason_codes == ("selection_scorer_aligned",)
    assert report.reason_code_divergence_counts == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_agreement_audit_marks_low_overlap_when_selected_rows_are_missing_from_scorer() -> None:
    agreement = _module()
    selection = _selection_report(
        (
            _selection_row("alpha", "cond-alpha"),
            _selection_row("beta", "cond-beta"),
        ),
    )
    scorer = _scorer_report((_scorer_candidate("alpha", "cond-alpha"),))

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.selected_count == 2
    assert report.scorer_candidate_count == 1
    assert report.selected_market_overlap_count == 1
    assert report.selected_condition_overlap_count == 1
    assert report.agreement_status == "low_overlap"
    assert report.recommended_next_step == "review_selection_scorer_disagreement"
    assert "low_selection_scorer_overlap" in report.reason_codes


def test_agreement_audit_ignores_blocked_scorer_rows_for_selected_overlap() -> None:
    agreement = _module()
    selection = _selection_report(
        selected_rows=(_selection_row("alpha", "cond-alpha"),),
    )
    scorer = _scorer_report(
        (
            _scorer_candidate("alpha", "cond-alpha", status="blocked"),
            _scorer_candidate("beta", "cond-beta"),
        ),
    )

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.selected_count == 1
    assert report.scorer_candidate_count == 2
    assert report.selected_market_overlap_count == 0
    assert report.selected_condition_overlap_count == 0
    assert report.scored_but_unselected_count == 1
    assert report.agreement_status == "low_overlap"
    assert "low_selection_scorer_overlap" in report.reason_codes
    assert "scored_but_unselected" in report.reason_codes


def test_agreement_audit_selected_rows_none_falls_back_without_force_selecting_rows() -> None:
    agreement = _module()
    selection = SimpleNamespace(
        generated_at=SELECTION_AT,
        selected_rows=None,
        rows=(
            _selection_row("alpha", "cond-alpha"),
            _selection_row(
                "beta",
                "cond-beta",
                status="rejected",
                action="reject",
                recommendation="reject",
            ),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    scorer = _scorer_report((_scorer_candidate("alpha", "cond-alpha"),))

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.selected_count == 1
    assert report.selected_market_overlap_count == 1
    assert report.selected_condition_overlap_count == 1
    assert report.rejected_but_scored_count == 0
    assert report.scored_but_unselected_count == 0
    assert report.agreement_status == "aligned"


def test_agreement_audit_prioritizes_blocked_scorer_gate() -> None:
    agreement = _module()
    selection = _selection_report((_selection_row("alpha", "cond-alpha"),))
    scorer = _scorer_report((), gate_status="blocked")

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.scorer_gate_status == "blocked"
    assert report.agreement_status == "gate_blocked"
    assert report.recommended_next_step == "review_scorer_gate"
    assert report.reason_codes == ("scorer_gate_blocked",)


def test_agreement_audit_requests_enrichment_when_source_inputs_are_missing() -> None:
    agreement = _module()

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=None,
        scorer_input=None,
        generated_at=GENERATED_AT,
    )

    assert report.selection_generated_at is None
    assert report.scorer_generated_at is None
    assert report.selected_count == 0
    assert report.scorer_candidate_count == 0
    assert report.agreement_status == "missing_inputs"
    assert report.recommended_next_step == "enrich_inputs"
    assert report.reason_codes == ("missing_inputs",)


def test_agreement_audit_requests_enrichment_when_identifiers_are_insufficient() -> None:
    agreement = _module()
    selection = _selection_report((_selection_row(None, None),))
    scorer = _scorer_report((_scorer_candidate(None, None),))

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.selected_count == 1
    assert report.scorer_candidate_count == 1
    assert report.selected_market_overlap_count == 0
    assert report.selected_condition_overlap_count == 0
    assert report.agreement_status == "insufficient_identifiers"
    assert report.recommended_next_step == "enrich_inputs"
    assert report.reason_codes == ("insufficient_identifiers",)


def test_agreement_audit_counts_rejected_rows_that_were_scored() -> None:
    agreement = _module()
    selection = _selection_report(
        (
            _selection_row("alpha", "cond-alpha"),
            _selection_row(
                "beta",
                "cond-beta",
                status="rejected",
                action="reject",
                recommendation="reject",
                reason_codes=("selection_rejected",),
            ),
        ),
    )
    scorer = _scorer_report(
        (
            _scorer_candidate("alpha", "cond-alpha"),
            _scorer_candidate("beta", "cond-beta", reason_codes=("scorer_scored",)),
        ),
    )

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.selected_count == 1
    assert report.selected_market_overlap_count == 1
    assert report.rejected_but_scored_count == 1
    assert report.scored_but_unselected_count == 1
    assert report.agreement_status == "aligned"
    assert "rejected_but_scored" in report.reason_codes
    assert "scored_but_unselected" in report.reason_codes


def test_agreement_audit_counts_reason_code_divergence() -> None:
    agreement = _module()
    selection = _selection_report(
        (
            _selection_row(
                "alpha",
                "cond-alpha",
                reason_codes=("cost_ok", "edge_passed"),
            ),
        ),
    )
    scorer = _scorer_report(
        (
            _scorer_candidate(
                "alpha",
                "cond-alpha",
                reason_codes=("edge_passed", "model_passed"),
            ),
        ),
    )

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.reason_code_divergence_counts == (
        ("cost_ok", 1),
        ("model_passed", 1),
    )
    assert "reason_code_divergence" in report.reason_codes


def test_agreement_audit_treats_condition_mismatch_as_unaligned_even_when_market_matches() -> None:
    agreement = _module()
    selection = _selection_report(
        (
            _selection_row(
                "alpha",
                "cond-selection",
                reason_codes=("selection_reason",),
            ),
        ),
    )
    scorer = _scorer_report(
        (
            _scorer_candidate(
                "alpha",
                "cond-scorer",
                reason_codes=("scorer_reason",),
            ),
        ),
    )

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.selected_market_overlap_count == 1
    assert report.selected_condition_overlap_count == 0
    assert report.scored_but_unselected_count == 1
    assert report.agreement_status == "low_overlap"
    assert report.reason_code_divergence_counts == ()
    assert "scored_but_unselected" in report.reason_codes


def test_agreement_audit_counts_duplicate_selected_overlap_by_row() -> None:
    agreement = _module()
    selection = _selection_report(
        (
            _selection_row("alpha", "cond-alpha"),
            _selection_row("alpha", "cond-alpha"),
        ),
    )
    scorer = _scorer_report((_scorer_candidate("alpha", "cond-alpha"),))

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.selected_count == 2
    assert report.selected_market_overlap_count == 2
    assert report.selected_condition_overlap_count == 2
    assert report.agreement_status == "aligned"


def test_agreement_audit_rejects_float_inside_report_like_source_rows() -> None:
    agreement = _module()
    row = _selection_row("alpha", "cond-alpha")
    row.probability = 0.1

    with pytest.raises(ValueError, match="float"):
        agreement.build_probability_selection_scorer_agreement_report(
            selection_input=_selection_report((row,)),
            scorer_input=_scorer_report((_scorer_candidate("alpha", "cond-alpha"),)),
            generated_at=GENERATED_AT,
        )


@dataclass(frozen=True)
class _NestedAuditValues:
    probabilities: list[object]


def test_agreement_audit_accepts_nested_decimal_values_in_source_trees() -> None:
    agreement = _module()
    selection = _selection_report((_selection_row("alpha", "cond-alpha"),))
    selection.config = SimpleNamespace(
        thresholds={"min_edge": [Decimal("0.010000")]},
    )
    selection.audit_values = _NestedAuditValues(
        probabilities=[Decimal("0.510000")],
    )
    scorer = _scorer_report((_scorer_candidate("alpha", "cond-alpha"),))
    scorer.report_values = {"scores": [_NestedAuditValues([Decimal("0.730000")])]}

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=selection,
        scorer_input=scorer,
        generated_at=GENERATED_AT,
    )

    assert report.agreement_status == "aligned"


@pytest.mark.parametrize(
    ("source_name", "field_name", "field_value"),
    (
        ("selection", "config", SimpleNamespace(thresholds={"min_edge": [0.01]})),
        ("selection", "audit_values", _NestedAuditValues(probabilities=[0.51])),
        ("scorer", "report_values", {"scores": [_NestedAuditValues([0.73])]}),
    ),
)
def test_agreement_audit_rejects_nested_float_values_in_source_trees(
    source_name: str,
    field_name: str,
    field_value: object,
) -> None:
    agreement = _module()
    selection = _selection_report((_selection_row("alpha", "cond-alpha"),))
    scorer = _scorer_report((_scorer_candidate("alpha", "cond-alpha"),))
    source = selection if source_name == "selection" else scorer
    setattr(source, field_name, field_value)

    with pytest.raises(ValueError, match="float"):
        agreement.build_probability_selection_scorer_agreement_report(
            selection_input=selection,
            scorer_input=scorer,
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize(
    ("placement", "decimal_value"),
    (
        ("source_config", Decimal("NaN")),
        ("source_row", Decimal("Infinity")),
        ("report_values", Decimal("-Infinity")),
    ),
)
def test_agreement_audit_rejects_non_finite_decimal_values_in_source_trees(
    placement: str,
    decimal_value: Decimal,
) -> None:
    agreement = _module()
    row = _selection_row("alpha", "cond-alpha")
    selection = _selection_report((row,))
    scorer = _scorer_report((_scorer_candidate("alpha", "cond-alpha"),))
    if placement == "source_config":
        selection.config = SimpleNamespace(
            thresholds={"min_edge": [decimal_value]},
        )
    elif placement == "source_row":
        row.audit_values = _NestedAuditValues(probabilities=[decimal_value])
    else:
        scorer.report_values = {
            "scores": [_NestedAuditValues(probabilities=[decimal_value])],
        }

    with pytest.raises(ValueError, match="finite"):
        agreement.build_probability_selection_scorer_agreement_report(
            selection_input=selection,
            scorer_input=scorer,
            generated_at=GENERATED_AT,
        )


def test_agreement_audit_rejects_float_mapping_keys_in_source_metadata() -> None:
    agreement = _module()
    selection = _selection_report((_selection_row("alpha", "cond-alpha"),))
    selection.metadata = {0.5: "float-key"}

    with pytest.raises(ValueError, match="float"):
        agreement.build_probability_selection_scorer_agreement_report(
            selection_input=selection,
            scorer_input=_scorer_report((_scorer_candidate("alpha", "cond-alpha"),)),
            generated_at=GENERATED_AT,
        )


def test_agreement_audit_rejects_negative_selected_count_even_with_rows() -> None:
    agreement = _module()
    selection = _selection_report((_selection_row("alpha", "cond-alpha"),))
    selection.selected_count = -1

    with pytest.raises(ValueError, match="selected_count"):
        agreement.build_probability_selection_scorer_agreement_report(
            selection_input=selection,
            scorer_input=_scorer_report((_scorer_candidate("alpha", "cond-alpha"),)),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("count_field", ("candidate_count", "markets_scored"))
def test_agreement_audit_rejects_negative_scorer_count_even_with_candidates(
    count_field: str,
) -> None:
    agreement = _module()
    scorer = _scorer_report((_scorer_candidate("alpha", "cond-alpha"),))
    setattr(scorer, count_field, -1)

    with pytest.raises(ValueError, match=count_field):
        agreement.build_probability_selection_scorer_agreement_report(
            selection_input=_selection_report((_selection_row("alpha", "cond-alpha"),)),
            scorer_input=scorer,
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_agreement_audit_rejects_false_source_report_flags(flag_name: str) -> None:
    agreement = _module()
    selection = _selection_report((_selection_row("alpha", "cond-alpha"),))
    setattr(selection, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        agreement.build_probability_selection_scorer_agreement_report(
            selection_input=selection,
            scorer_input=_scorer_report((_scorer_candidate("alpha", "cond-alpha"),)),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_agreement_audit_rejects_false_source_row_flags(flag_name: str) -> None:
    agreement = _module()
    row = _selection_row("alpha", "cond-alpha")
    setattr(row, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        agreement.build_probability_selection_scorer_agreement_report(
            selection_input=_selection_report((row,)),
            scorer_input=_scorer_report((_scorer_candidate("alpha", "cond-alpha"),)),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_agreement_audit_rejects_false_scorer_flags(flag_name: str) -> None:
    agreement = _module()
    scorer = _scorer_report((_scorer_candidate("alpha", "cond-alpha"),))
    setattr(scorer, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        agreement.build_probability_selection_scorer_agreement_report(
            selection_input=_selection_report((_selection_row("alpha", "cond-alpha"),)),
            scorer_input=scorer,
            generated_at=GENERATED_AT,
        )


def test_agreement_audit_rejects_false_config_flags() -> None:
    agreement = _module()

    with pytest.raises(ValueError, match="paper_only"):
        agreement.ProbabilitySelectionScorerAgreementConfig(paper_only=False)


def test_agreement_audit_config_rejects_float_overlap_share() -> None:
    agreement = _module()

    with pytest.raises(ValueError, match="min_selected_overlap_share"):
        agreement.ProbabilitySelectionScorerAgreementConfig(
            min_selected_overlap_share=1.0,
        )


def test_agreement_audit_dataclasses_are_frozen() -> None:
    agreement = _module()
    config = agreement.ProbabilitySelectionScorerAgreementConfig()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"

    report = agreement.build_probability_selection_scorer_agreement_report(
        selection_input=None,
        scorer_input=None,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.agreement_status = "changed"


def test_agreement_audit_config_does_not_support_subclassing() -> None:
    agreement = _module()

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadConfig(agreement.ProbabilitySelectionScorerAgreementConfig):
            pass


def test_agreement_audit_report_does_not_support_subclassing() -> None:
    agreement = _module()

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReport(agreement.ProbabilitySelectionScorerAgreementReport):
            pass


def test_agreement_audit_config_post_init_requires_exact_type() -> None:
    agreement = _module()
    config_like = SimpleNamespace(
        config_version="probability-selection-scorer-agreement-v0",
        min_selected_overlap_share=Decimal("1.000000"),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    with pytest.raises(
        ValueError,
        match="exactly ProbabilitySelectionScorerAgreementConfig",
    ):
        agreement.ProbabilitySelectionScorerAgreementConfig.__post_init__(config_like)


def test_agreement_audit_report_post_init_requires_exact_type() -> None:
    agreement = _module()
    report_like = SimpleNamespace(
        generated_at=GENERATED_AT,
        config_version="probability-selection-scorer-agreement-v0",
        selection_generated_at=None,
        scorer_generated_at=None,
        selected_count=0,
        scorer_candidate_count=0,
        selected_market_overlap_count=0,
        selected_condition_overlap_count=0,
        rejected_but_scored_count=0,
        scored_but_unselected_count=0,
        scorer_gate_status="pass",
        agreement_status="aligned",
        recommended_next_step="continue_monitoring",
        reason_codes=("selection_scorer_aligned",),
        reason_code_divergence_counts=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    with pytest.raises(
        ValueError,
        match="exactly ProbabilitySelectionScorerAgreementReport",
    ):
        agreement.ProbabilitySelectionScorerAgreementReport.__post_init__(report_like)
