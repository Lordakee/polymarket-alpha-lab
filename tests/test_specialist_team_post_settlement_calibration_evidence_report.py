from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_post_settlement_calibration_evidence_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_post_settlement_calibration_evidence_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(**overrides: object):
    module = api()
    values = {
        "team_id": "team_politics",
        "category_id": "category_politics",
        "settled_prediction_count": d("12.000000"),
        "mean_probability_error": d("0.040000"),
        "source_error_count": d("0.000000"),
        "memory_update_required": False,
    }
    values.update(overrides)
    return module.SpecialistTeamPostSettlementCalibrationEvidenceSignal(**values)


def report(*signals: object):
    module = api()
    return module.build_specialist_team_post_settlement_calibration_evidence_report(
        signals,
        config=module.SpecialistTeamPostSettlementCalibrationEvidenceConfig(),
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def test_build_report_outputs_calibration_status_reason_codes_and_manual_steps() -> None:
    module = api()
    inputs = (
        signal(
            team_id="team_crypto",
            category_id="category_crypto",
            settled_prediction_count=d("7.000000"),
            mean_probability_error=d("0.100000"),
            source_error_count=d("1.000000"),
            memory_update_required=True,
        ),
        signal(
            team_id="team_equities",
            category_id="category_equities",
            settled_prediction_count=d("2.000000"),
            mean_probability_error=d("0.220000"),
            source_error_count=d("3.000000"),
            memory_update_required=True,
        ),
        signal(
            team_id="team_politics",
            category_id="category_politics",
            settled_prediction_count=d("12.000000"),
            mean_probability_error=d("0.040000"),
            source_error_count=d("0.000000"),
            memory_update_required=False,
        ),
    )

    result = report(*inputs)

    assert is_dataclass(result)
    assert module.SPECIALIST_TEAM_POST_SETTLEMENT_CALIBRATION_EVIDENCE_STATUSES == (
        "sufficient",
        "review",
        "insufficient",
    )
    assert result.report_status == "insufficient"
    assert result.row_count == d("3.000000")
    assert result.sufficient_count == d("1.000000")
    assert result.review_count == d("1.000000")
    assert result.insufficient_count == d("1.000000")
    assert [row.team_id for row in result.rows] == [
        "team_politics",
        "team_crypto",
        "team_equities",
    ]
    assert [row.calibration_evidence_status for row in result.rows] == [
        "sufficient",
        "review",
        "insufficient",
    ]
    assert [row.manual_next_step for row in result.rows] == [
        "archive_post_settlement_calibration_evidence",
        "manual_review_calibration_evidence_before_memory_update",
        "manual_collect_settled_calibration_evidence_before_any_model_change",
    ]
    assert result.rows[0].reason_codes == ("calibration_evidence_sufficient",)
    assert result.rows[1].reason_codes == (
        "calibration_evidence_review",
        "memory_update_required",
        "source_error_observed",
    )
    assert result.rows[2].reason_codes == (
        "calibration_evidence_insufficient",
        "insufficient_settled_predictions",
        "memory_update_required",
        "probability_error_above_review_threshold",
        "source_error_observed",
    )
    assert result.reason_codes == (
        "calibration_evidence_insufficient",
        "calibration_evidence_review",
        "calibration_evidence_sufficient",
        "insufficient_settled_predictions",
        "memory_update_required",
        "probability_error_above_review_threshold",
        "source_error_observed",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in result.rows)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_empty_report_blocks_manual_collection_without_side_effects() -> None:
    module = api()
    result = report()

    assert result.report_status == "insufficient"
    assert result.row_count == d("0.000000")
    assert result.reason_codes == ("no_post_settlement_calibration_evidence",)
    assert result.reason_code_counts == (
        module.SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount(
            reason_code="no_post_settlement_calibration_evidence",
            count=d("1.000000"),
        ),
    )
    assert result.rows == ()
    assert result.manual_next_step == (
        "manual_collect_settled_calibration_evidence_before_any_model_change"
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_is_json_ready_decimal_only_and_public_safe() -> None:
    module = api()
    result = report(
        signal(team_id="team_crypto", category_id="category_crypto"),
        signal(
            team_id="team_politics",
            category_id="category_politics",
            settled_prediction_count=d("4.000000"),
            mean_probability_error=d("0.160000"),
            source_error_count=d("1.000000"),
            memory_update_required=True,
        ),
    )

    payload = module.specialist_team_post_settlement_calibration_evidence_report_payload(
        result,
    )
    assert payload == result.payload
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    assert module.validate_specialist_team_post_settlement_calibration_evidence_report_payload(
        payload,
    )

    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "persist",
        "database",
        "live",
        "auth",
        "wallet",
        "order",
        "trade",
        "execute",
        "execution",
        "token",
        "secret",
        "api_key",
        "private_key",
        "adjust",
        "tune",
        "retune",
        "parameter",
    ):
        assert forbidden not in encoded


def test_validation_requires_decimal_counts_codes_flags_and_frozen_outputs() -> None:
    module = api()
    result = report(signal())

    with pytest.raises(FrozenInstanceError):
        result.report_status = "review"  # type: ignore[misc]

    with pytest.raises(ValueError, match="settled_prediction_count must be a Decimal"):
        signal(settled_prediction_count=12)

    with pytest.raises(ValueError, match="mean_probability_error must be a Decimal"):
        signal(mean_probability_error=_DecimalSubclass("0.040000"))

    with pytest.raises(ValueError, match="source_error_count must be an integer Decimal"):
        signal(source_error_count=d("1.500000"))

    with pytest.raises(ValueError, match="mean_probability_error must be between"):
        signal(mean_probability_error=d("1.000001"))

    with pytest.raises(ValueError, match="memory_update_required must be a bool"):
        signal(memory_update_required=1)

    with pytest.raises(ValueError, match="team_id must be a public code"):
        signal(team_id="Team Politics")

    with pytest.raises(ValueError, match="category_id must be a public code"):
        signal(category_id="market-politics")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(signal(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="calibration_evidence_status must be supported"):
        module.SpecialistTeamPostSettlementCalibrationEvidenceRow(
            team_id="team_politics",
            category_id="category_politics",
            settled_prediction_count=d("12.000000"),
            mean_probability_error=d("0.040000"),
            source_error_count=d("0.000000"),
            memory_update_required=False,
            calibration_evidence_status="approved",
            reason_codes=("calibration_evidence_sufficient",),
            manual_next_step="archive_post_settlement_calibration_evidence",
        )


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "minimum_sufficient_settled_prediction_count",
        "minimum_review_settled_prediction_count",
        "maximum_sufficient_mean_probability_error",
        "maximum_review_mean_probability_error",
        "settled_prediction_count",
        "mean_probability_error",
        "source_error_count",
        "row_count",
        "team_count",
        "category_count",
        "sufficient_count",
        "review_count",
        "insufficient_count",
        "manual_next_step_count",
        "count",
    }

    for cls in (
        module.SpecialistTeamPostSettlementCalibrationEvidenceConfig,
        module.SpecialistTeamPostSettlementCalibrationEvidenceSignal,
        module.SpecialistTeamPostSettlementCalibrationEvidenceRow,
        module.SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount,
        module.SpecialistTeamPostSettlementCalibrationEvidenceReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in decimal_fields:
                assert hints[item.name] is Decimal


def test_payload_validation_rejects_tampering_and_unsafe_numeric_values() -> None:
    module = api()
    payload = report(signal()).payload

    tampered = dict(payload)
    tampered["report_status"] = "review"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_specialist_team_post_settlement_calibration_evidence_report_payload(
            tampered,
        )

    unsafe_numeric = dict(payload)
    unsafe_numeric["row_count"] = 1
    with pytest.raises(ValueError, match="numeric payload values must be Decimal strings"):
        module.validate_specialist_team_post_settlement_calibration_evidence_report_payload(
            unsafe_numeric,
        )


def test_module_does_not_import_side_effect_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    forbidden_import_fragments = (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "web3",
        "wallet",
        "order",
        "auth",
        "live",
    )
    assert not any(
        fragment in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
