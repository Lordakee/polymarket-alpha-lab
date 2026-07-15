from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_DOWN, localcontext
import hashlib
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_team_specialist_learning_velocity_report as api
from polymarket_alpha_lab.research_team_specialist_learning_velocity_report import (
    ResearchTeamSpecialistLearningVelocityConfig,
    ResearchTeamSpecialistLearningVelocityDomainFeedback,
    ResearchTeamSpecialistLearningVelocityDomainRow,
    ResearchTeamSpecialistLearningVelocityPublicPayloadItem,
    ResearchTeamSpecialistLearningVelocityReport,
    build_research_team_specialist_learning_velocity_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_learning_velocity_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def _feedback(
    *,
    domain_key: str = "macro",
    specialist_team_key: str = "macro_team",
    resolved_outcome_feedback_count: Decimal = d("8.000000"),
    correction_follow_through_rate: Decimal = d("0.900000"),
    memory_age_seconds: Decimal = d("86400.000000"),
    calibration_drift: Decimal = d("0.020000"),
    workload_pressure: Decimal = d("0.300000"),
    observed_at: datetime = NOW,
    feedback_config_version: str = "feedback-v1",
) -> ResearchTeamSpecialistLearningVelocityDomainFeedback:
    return ResearchTeamSpecialistLearningVelocityDomainFeedback(
        domain_key=domain_key,
        specialist_team_key=specialist_team_key,
        observed_at=observed_at,
        resolved_outcome_feedback_count=resolved_outcome_feedback_count,
        correction_follow_through_rate=correction_follow_through_rate,
        memory_age_seconds=memory_age_seconds,
        calibration_drift=calibration_drift,
        workload_pressure=workload_pressure,
        feedback_config_version=feedback_config_version,
    )


def _report(
    feedback: tuple[ResearchTeamSpecialistLearningVelocityDomainFeedback, ...],
    *,
    config: ResearchTeamSpecialistLearningVelocityConfig | None = None,
    public_payload: tuple[ResearchTeamSpecialistLearningVelocityPublicPayloadItem, ...] = (),
) -> ResearchTeamSpecialistLearningVelocityReport:
    return build_research_team_specialist_learning_velocity_report(
        feedback,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def _unsafe_json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _unsafe_json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_unsafe_json_ready(item) for item in value]
    if type(value) is dict:
        return {
            key: _unsafe_json_ready(item)
            for key, item in value.items()
        }
    return value


def _resign_report_unsafe(
    report: ResearchTeamSpecialistLearningVelocityReport,
) -> None:
    values = {
        field.name: _unsafe_json_ready(getattr(report, field.name))
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    digest = hashlib.sha256(
        json.dumps(
            values,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    object.__setattr__(report, "derived_validation_digest", digest)


def _resign_public_mapping(payload: dict[str, object]) -> None:
    unsigned = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            unsigned,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def test_reports_learning_velocity_by_domain_with_only_pass_watch_block_statuses() -> None:
    report = _report(
        (
            _feedback(domain_key="macro", specialist_team_key="macro_team"),
            _feedback(
                domain_key="crypto",
                specialist_team_key="crypto_team",
                resolved_outcome_feedback_count=d("3.000000"),
                correction_follow_through_rate=d("0.650000"),
                memory_age_seconds=d("1728000.000000"),
                calibration_drift=d("0.070000"),
                workload_pressure=d("0.600000"),
            ),
            _feedback(
                domain_key="sports",
                specialist_team_key="sports_team",
                resolved_outcome_feedback_count=d("0.000000"),
                correction_follow_through_rate=d("0.400000"),
                memory_age_seconds=d("8640000.000000"),
                calibration_drift=d("0.150000"),
                workload_pressure=d("0.950000"),
            ),
        ),
    )

    rows = {row.domain_key: row for row in report.rows}
    assert report.report_status == "block"
    assert report.domain_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert set(rows) == {"crypto", "macro", "sports"}

    assert rows["macro"].learning_velocity_score == d("0.880000")
    assert rows["macro"].velocity_status == "pass"
    assert rows["macro"].reason_codes == ("specialist_learning_velocity_pass",)

    assert rows["crypto"].learning_velocity_score == d("0.521796")
    assert rows["crypto"].velocity_status == "watch"
    assert "resolved_feedback_depth_watch" in rows["crypto"].reason_codes
    assert "calibration_drift_watch" in rows["crypto"].reason_codes

    assert rows["sports"].learning_velocity_score == d("0.090000")
    assert rows["sports"].velocity_status == "block"
    assert "resolved_feedback_missing" in rows["sports"].reason_codes
    assert "memory_freshness_block" in rows["sports"].reason_codes
    assert "workload_pressure_block" in rows["sports"].reason_codes
    assert {row.velocity_status for row in report.rows} == {"pass", "watch", "block"}
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("memory_age_seconds", "expected_score"),
    (
        ("604800.000000", "1.000000"),
        ("2613600.000000", "0.750000"),
        ("4622400.000000", "0.500000"),
        ("6631200.000000", "0.250000"),
        ("8640000.000000", "0.000000"),
    ),
)
def test_memory_freshness_interpolates_continuously_between_watch_and_block(
    memory_age_seconds: str,
    expected_score: str,
) -> None:
    config = ResearchTeamSpecialistLearningVelocityConfig()

    assert api._memory_freshness_score(
        d(memory_age_seconds),
        config,
    ) == d(expected_score)


@pytest.mark.parametrize(
    ("field_name", "value", "expected_status", "expected_reason_code"),
    (
        ("memory_age_seconds", "604800.000000", "pass", None),
        (
            "memory_age_seconds",
            "604801.000000",
            "watch",
            "memory_freshness_watch",
        ),
        (
            "memory_age_seconds",
            "8640000.000000",
            "block",
            "memory_freshness_block",
        ),
        ("calibration_drift", "0.050000", "pass", None),
        (
            "calibration_drift",
            "0.050001",
            "watch",
            "calibration_drift_watch",
        ),
        (
            "calibration_drift",
            "0.100000",
            "block",
            "calibration_drift_block",
        ),
        ("workload_pressure", "0.500000", "pass", None),
        (
            "workload_pressure",
            "0.500001",
            "watch",
            "workload_pressure_watch",
        ),
        (
            "workload_pressure",
            "0.850000",
            "block",
            "workload_pressure_block",
        ),
    ),
)
def test_public_rows_lock_watch_and_block_threshold_boundaries(
    field_name: str,
    value: str,
    expected_status: str,
    expected_reason_code: str | None,
) -> None:
    row = _report((_feedback(**{field_name: d(value)}),)).rows[0]

    assert row.velocity_status == expected_status
    if expected_reason_code is None:
        assert row.reason_codes == ("specialist_learning_velocity_pass",)
    else:
        assert expected_reason_code in row.reason_codes


@pytest.mark.parametrize(
    ("learning_velocity_score", "expected_status"),
    (
        ("0.250000", "block"),
        ("0.250001", "watch"),
        ("0.499999", "watch"),
        ("0.500000", "pass"),
    ),
)
def test_learning_velocity_score_threshold_boundaries_are_inclusive(
    learning_velocity_score: str,
    expected_status: str,
) -> None:
    config = ResearchTeamSpecialistLearningVelocityConfig()

    assert api._row_status(
        learning_velocity_score=d(learning_velocity_score),
        reason_codes=(),
        config=config,
    ) == expected_status


def test_payload_is_deterministic_decimal_stringified_and_digest_validated() -> None:
    feedback = (
        _feedback(domain_key="macro", specialist_team_key="macro_team"),
        _feedback(
            domain_key="crypto",
            specialist_team_key="crypto_team",
            resolved_outcome_feedback_count=d("3.000000"),
            correction_follow_through_rate=d("0.650000"),
            memory_age_seconds=d("1728000.000000"),
            calibration_drift=d("0.070000"),
            workload_pressure=d("0.600000"),
        ),
    )
    report = _report(
        feedback,
        public_payload=(
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                key="safe_note",
                value="learning loop audit",
            ),
        ),
    )
    reordered = _report(tuple(reversed(feedback)), public_payload=report.public_payload)

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload == reordered.payload
    assert payload["domain_count"] == "2.000000"
    assert payload["average_learning_velocity_score"] == "0.700898"
    assert payload["rows"][0]["learning_velocity_score"] == "0.521796"
    assert payload["rows"][1]["learning_velocity_score"] == "0.880000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert report.derived_validation_digest == reordered.derived_validation_digest
    assert "market" not in json.dumps(payload, sort_keys=True).lower()
    assert "candidate" not in json.dumps(payload, sort_keys=True).lower()
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_equal_score_rows_use_complete_stable_tie_breakers() -> None:
    lower_correction = _feedback(
        domain_key="zeta",
        specialist_team_key="team_z",
        correction_follow_through_rate=d("0.800000"),
        workload_pressure=d("0.200000"),
    )
    higher_correction = _feedback(
        domain_key="alpha",
        specialist_team_key="team_a",
        correction_follow_through_rate=d("0.900000"),
        workload_pressure=d("0.308565"),
    )

    first = _report((higher_correction, lower_correction))
    second = _report((lower_correction, higher_correction))

    assert {row.learning_velocity_score for row in first.rows} == {d("0.879144")}
    assert tuple(row.domain_key for row in first.rows) == ("zeta", "alpha")
    assert first.rows == second.rows
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest


def test_public_payload_and_digest_api_use_canonical_public_payload() -> None:
    report = _report(
        (_feedback(),),
        public_payload=(
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                key="safe_note",
                value="learning loop audit",
            ),
        ),
    )

    payload = api.research_team_specialist_learning_velocity_report_payload(report)
    digest_values = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_values,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()

    assert payload == report.payload
    assert (
        api.research_team_specialist_learning_velocity_report_digest(report)
        == expected_digest
        == report.derived_validation_digest
    )


def test_reason_code_counts_are_public_canonical_and_derived_from_rows() -> None:
    reason_count_type = api.ResearchTeamSpecialistLearningVelocityReasonCodeCount
    report = _report(
        (
            _feedback(
                domain_key="crypto",
                memory_age_seconds=d("604801.000000"),
            ),
            _feedback(
                domain_key="sports",
                memory_age_seconds=d("604802.000000"),
            ),
        ),
    )

    assert tuple(field.name for field in fields(reason_count_type)) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert report.reason_code_counts == (
        reason_count_type(
            reason_code="memory_freshness_watch",
            count=d("2.000000"),
        ),
    )
    assert tuple(item.reason_code for item in report.reason_code_counts) == report.reason_codes


def test_public_mapping_round_trip_uses_ordered_schema_and_sha256() -> None:
    report = _report(
        (_feedback(),),
        public_payload=(
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                key="safe_note",
                value="learning loop audit",
            ),
        ),
    )
    payload = report.payload
    unsigned = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    expected_digest = hashlib.sha256(
        json.dumps(
            unsigned,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()

    assert tuple(payload) == tuple(
        field.name for field in fields(ResearchTeamSpecialistLearningVelocityReport)
    )
    assert tuple(payload["rows"][0]) == tuple(
        field.name for field in fields(ResearchTeamSpecialistLearningVelocityDomainRow)
    )
    assert tuple(payload["reason_code_counts"][0]) == tuple(
        field.name
        for field in fields(
            api.ResearchTeamSpecialistLearningVelocityReasonCodeCount,
        )
    )
    assert tuple(payload["public_payload"][0]) == tuple(
        field.name
        for field in fields(
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem,
        )
    )
    assert report.derived_validation_digest == expected_digest
    assert api.research_team_specialist_learning_velocity_report_payload(payload) == payload
    assert api.research_team_specialist_learning_velocity_report_digest(payload) == expected_digest
    api.validate_research_team_specialist_learning_velocity_report_payload(payload)


@pytest.mark.parametrize(
    "nested_field",
    ("rows", "reason_code_counts", "public_payload"),
)
def test_public_mapping_requires_exact_canonical_nested_key_order(
    nested_field: str,
) -> None:
    payload = _report(
        (_feedback(),),
        public_payload=(
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                key="safe_note",
                value="learning loop audit",
            ),
        ),
    ).payload
    forged = deepcopy(payload)
    forged[nested_field][0] = dict(reversed(tuple(forged[nested_field][0].items())))

    with pytest.raises(ValueError, match=rf"{nested_field}.*schema order"):
        api.research_team_specialist_learning_velocity_report_payload(forged)


def test_public_mapping_requires_exact_canonical_report_key_order() -> None:
    payload = _report((_feedback(),)).payload
    reordered = dict(reversed(tuple(payload.items())))

    with pytest.raises(ValueError, match="payload.*schema order"):
        api.research_team_specialist_learning_velocity_report_payload(reordered)

    extra = dict(payload)
    extra["unexpected"] = "value"
    with pytest.raises(ValueError, match="payload.*schema"):
        api.research_team_specialist_learning_velocity_report_payload(extra)


@pytest.mark.parametrize(
    "nested_field",
    (None, "rows", "reason_code_counts", "public_payload"),
)
def test_public_mapping_preserves_phase_one_flags_at_every_level(
    nested_field: str | None,
) -> None:
    payload = deepcopy(
        _report(
            (_feedback(),),
            public_payload=(
                ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                    key="safe_note",
                    value="learning loop audit",
                ),
            ),
        ).payload,
    )
    target = payload if nested_field is None else payload[nested_field][0]
    target["readonly"] = False
    _resign_public_mapping(payload)

    with pytest.raises(ValueError, match="readonly"):
        api.validate_research_team_specialist_learning_velocity_report_payload(payload)


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error"),
    (
        (
            "resolved_outcome_feedback_count",
            "3.000000",
            "resolved_feedback_depth_score",
        ),
        ("correction_follow_through_rate", "0.800000", "learning_velocity_score"),
        ("memory_age_seconds", "700000.000000", "memory_freshness_score"),
        ("calibration_drift", "0.030000", "calibration_stability_score"),
        ("workload_pressure", "0.400000", "workload_capacity_score"),
        ("resolved_feedback_depth_score", "0.500000", "resolved_feedback_depth_score"),
        ("memory_freshness_score", "0.500000", "memory_freshness_score"),
        (
            "calibration_stability_score",
            "0.500000",
            "calibration_stability_score",
        ),
        ("workload_capacity_score", "0.500000", "workload_capacity_score"),
        ("learning_velocity_score", "0.500000", "learning_velocity_score"),
        ("velocity_status", "watch", "velocity_status"),
        ("reason_codes", ["learning_velocity_score_watch"], "reason_codes"),
    ),
)
def test_resigned_public_mapping_rederives_all_row_observations_and_outputs(
    field_name: str,
    forged_value: object,
    error: str,
) -> None:
    payload = deepcopy(_report((_feedback(),)).payload)
    payload["rows"][0][field_name] = forged_value
    _resign_public_mapping(payload)

    with pytest.raises(ValueError, match=error):
        api.validate_research_team_specialist_learning_velocity_report_payload(payload)


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("report_status", "watch"),
        ("domain_count", "2.000000"),
        ("pass_count", "0.000000"),
        ("watch_count", "1.000000"),
        ("block_count", "1.000000"),
        ("average_learning_velocity_score", "0.500000"),
        ("min_learning_velocity_score", "0.500000"),
        ("max_workload_pressure", "0.400000"),
        ("max_memory_age_seconds", "86401.000000"),
        ("feedback_config_versions", [["macro", "feedback-forged"]]),
        ("reason_codes", ["learning_velocity_score_watch"]),
    ),
)
def test_resigned_public_mapping_rederives_all_report_aggregates(
    field_name: str,
    forged_value: object,
) -> None:
    payload = deepcopy(_report((_feedback(),)).payload)
    payload[field_name] = forged_value
    _resign_public_mapping(payload)

    with pytest.raises(ValueError, match=field_name):
        api.validate_research_team_specialist_learning_velocity_report_payload(payload)


def test_resigned_public_mapping_rederives_reason_counts_and_row_order() -> None:
    report = _report(
        (
            _feedback(domain_key="macro", specialist_team_key="macro_team"),
            _feedback(
                domain_key="crypto",
                specialist_team_key="crypto_team",
                memory_age_seconds=d("604801.000000"),
            ),
        ),
    )

    forged_count = deepcopy(report.payload)
    forged_count["reason_code_counts"][0]["count"] = "9.000000"
    _resign_public_mapping(forged_count)
    with pytest.raises(ValueError, match="reason_code_counts"):
        api.validate_research_team_specialist_learning_velocity_report_payload(
            forged_count,
        )

    forged_order = deepcopy(report.payload)
    forged_order["rows"] = list(reversed(forged_order["rows"]))
    _resign_public_mapping(forged_order)
    with pytest.raises(ValueError, match="canonical row order"):
        api.validate_research_team_specialist_learning_velocity_report_payload(
            forged_order,
        )


def test_payload_revalidates_nested_row_and_reason_count_object_tampering() -> None:
    report = _report((_feedback(),))
    object.__setattr__(report.rows[0], "domain_key", "changed_domain")
    object.__setattr__(
        report,
        "feedback_config_versions",
        (("changed_domain", "feedback-v1"),),
    )
    _resign_report_unsafe(report)
    with pytest.raises(ValueError, match="domain_key"):
        _ = report.payload

    report = _report((_feedback(),))
    object.__setattr__(report.reason_code_counts[0], "count", d("9.000000"))
    _resign_report_unsafe(report)
    with pytest.raises(ValueError, match="count|reason_code_counts"):
        _ = report.payload


def test_row_sort_key_covers_every_non_flag_public_row_field() -> None:
    row = _report((_feedback(),)).rows[0]

    assert api._row_sort_key(row) == (
        api._STATUS_RANK[row.velocity_status],
        row.learning_velocity_score,
        row.resolved_feedback_depth_score,
        row.correction_follow_through_rate,
        row.memory_freshness_score,
        row.calibration_stability_score,
        row.workload_capacity_score,
        row.resolved_outcome_feedback_count,
        row.memory_age_seconds,
        row.calibration_drift,
        row.workload_pressure,
        row.observed_at,
        row.reason_codes,
        row.domain_key,
        row.specialist_team_key,
        row.feedback_config_version,
    )
    assert len(api._row_sort_key(row)) == len(fields(row)) - 3


def test_public_api_and_dataclass_schemas_are_exact() -> None:
    assert api.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_LEARNING_VELOCITY_CONFIG_VERSION",
        "ResearchTeamSpecialistLearningVelocityConfig",
        "ResearchTeamSpecialistLearningVelocityDomainFeedback",
        "ResearchTeamSpecialistLearningVelocityDomainRow",
        "ResearchTeamSpecialistLearningVelocityPublicPayloadItem",
        "ResearchTeamSpecialistLearningVelocityReasonCodeCount",
        "ResearchTeamSpecialistLearningVelocityReport",
        "build_research_team_specialist_learning_velocity_report",
        "research_team_specialist_learning_velocity_report_digest",
        "research_team_specialist_learning_velocity_report_payload",
        "validate_research_team_specialist_learning_velocity_report_payload",
    )
    assert tuple(field.name for field in fields(ResearchTeamSpecialistLearningVelocityConfig)) == (
        "config_version",
        "min_resolved_outcome_feedback_count",
        "watch_learning_velocity_score",
        "block_learning_velocity_score",
        "watch_memory_age_seconds",
        "block_memory_age_seconds",
        "watch_calibration_drift",
        "block_calibration_drift",
        "watch_workload_pressure",
        "block_workload_pressure",
        "resolved_feedback_depth_weight",
        "correction_follow_through_weight",
        "memory_freshness_weight",
        "calibration_stability_weight",
        "workload_capacity_weight",
        "velocity_signal_penalty",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(
        field.name for field in fields(ResearchTeamSpecialistLearningVelocityDomainFeedback)
    ) == (
        "domain_key",
        "specialist_team_key",
        "observed_at",
        "resolved_outcome_feedback_count",
        "correction_follow_through_rate",
        "memory_age_seconds",
        "calibration_drift",
        "workload_pressure",
        "feedback_config_version",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(
        field.name for field in fields(ResearchTeamSpecialistLearningVelocityDomainRow)
    ) == (
        "domain_key",
        "specialist_team_key",
        "feedback_config_version",
        "observed_at",
        "resolved_outcome_feedback_count",
        "resolved_feedback_depth_score",
        "correction_follow_through_rate",
        "memory_age_seconds",
        "memory_freshness_score",
        "calibration_drift",
        "calibration_stability_score",
        "workload_pressure",
        "workload_capacity_score",
        "learning_velocity_score",
        "velocity_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(
        field.name for field in fields(
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem,
        )
    ) == (
        "key",
        "value",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(
        field.name
        for field in fields(
            api.ResearchTeamSpecialistLearningVelocityReasonCodeCount,
        )
    ) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(ResearchTeamSpecialistLearningVelocityReport)) == (
        "generated_at",
        "config_version",
        "report_status",
        "domain_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_learning_velocity_score",
        "min_learning_velocity_score",
        "max_workload_pressure",
        "max_memory_age_seconds",
        "rows",
        "feedback_config_versions",
        "reason_codes",
        "reason_code_counts",
        "public_payload",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )


@pytest.mark.parametrize(
    "public_dataclass",
    (
        ResearchTeamSpecialistLearningVelocityConfig,
        ResearchTeamSpecialistLearningVelocityDomainFeedback,
        ResearchTeamSpecialistLearningVelocityDomainRow,
        ResearchTeamSpecialistLearningVelocityPublicPayloadItem,
        api.ResearchTeamSpecialistLearningVelocityReasonCodeCount,
        ResearchTeamSpecialistLearningVelocityReport,
    ),
)
def test_all_public_dataclasses_are_non_subclassable(public_dataclass: type[object]) -> None:
    with pytest.raises(TypeError):
        type(f"Derived{public_dataclass.__name__}", (public_dataclass,), {})


def test_payload_revalidates_strict_schema_after_instance_tampering() -> None:
    report = _report((_feedback(),))
    object.__setattr__(report, "domain_count", "1.000000")
    with pytest.raises(ValueError, match="domain_count.*Decimal"):
        _ = report.payload

    report = _report((_feedback(),))
    object.__setattr__(report.rows[0], "learning_velocity_score", "0.880000")
    with pytest.raises(ValueError, match="learning_velocity_score.*Decimal"):
        api.research_team_specialist_learning_velocity_report_digest(report)

    @dataclass(frozen=True)
    class UnknownPublicRow:
        safe_key: str

    report = _report((_feedback(),))
    object.__setattr__(report, "rows", (UnknownPublicRow("safe_value"),))
    with pytest.raises(
        ValueError,
        match="ResearchTeamSpecialistLearningVelocityDomainRow",
    ):
        api.research_team_specialist_learning_velocity_report_payload(report)


def test_public_payload_keys_must_be_unique() -> None:
    with pytest.raises(ValueError, match="public_payload.*key.*unique"):
        _report(
            (_feedback(),),
            public_payload=(
                ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                    key="safe_note",
                    value="first value",
                ),
                ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                    key="safe_note",
                    value="second value",
                ),
            ),
        )


def test_feedback_config_versions_are_recomputed_from_retained_public_rows() -> None:
    report = _report(
        (
            _feedback(domain_key="macro", feedback_config_version="feedback-v2"),
            _feedback(domain_key="sports", feedback_config_version="feedback-v3"),
        ),
    )

    expected = tuple(
        sorted(
            (row.domain_key, row.feedback_config_version)
            for row in report.rows
        ),
    )
    assert report.feedback_config_versions == expected


def test_payload_rejects_resigned_forged_feedback_config_versions() -> None:
    report = _report((_feedback(feedback_config_version="feedback-v1"),))
    object.__setattr__(
        report,
        "feedback_config_versions",
        (("macro", "feedback-forged"),),
    )
    _resign_report_unsafe(report)

    with pytest.raises(ValueError, match="feedback_config_versions.*rows"):
        _ = report.payload


def test_count_fields_require_whole_decimal_values() -> None:
    with pytest.raises(ValueError, match="min_resolved_outcome_feedback_count.*whole"):
        ResearchTeamSpecialistLearningVelocityConfig(
            min_resolved_outcome_feedback_count=d("4.500000"),
        )
    with pytest.raises(ValueError, match="resolved_outcome_feedback_count.*whole"):
        _feedback(resolved_outcome_feedback_count=d("1.500000"))
    with pytest.raises(ValueError, match="domain_count.*whole"):
        replace(_report((_feedback(),)), domain_count=d("1.500000"))


def test_reason_count_requires_exact_finite_unsigned_whole_decimal() -> None:
    reason_count_type = api.ResearchTeamSpecialistLearningVelocityReasonCodeCount

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="count.*Decimal"):
        reason_count_type(
            reason_code="specialist_learning_velocity_pass",
            count=DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="count.*signed zero"):
        reason_count_type(
            reason_code="specialist_learning_velocity_pass",
            count=d("-0.000000"),
        )
    with pytest.raises(ValueError, match="count.*whole"):
        reason_count_type(
            reason_code="specialist_learning_velocity_pass",
            count=d("1.500000"),
        )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("resolved_outcome_feedback_count", "-0.0000004", "nonnegative"),
        ("memory_age_seconds", "-0.0000004", "nonnegative"),
        ("correction_follow_through_rate", "-0.0000004", "between zero and one"),
        ("calibration_drift", "1.0000004", "between zero and one"),
        ("workload_pressure", "1.0000004", "between zero and one"),
    ),
)
def test_raw_bounds_are_checked_before_quantization(
    field_name: str,
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _feedback(**{field_name: d(value)})


def test_whole_decimal_requirement_is_checked_before_quantization() -> None:
    with pytest.raises(ValueError, match="resolved_outcome_feedback_count.*whole"):
        _feedback(resolved_outcome_feedback_count=d("1.0000004"))


def test_decimal_results_are_independent_of_ambient_context() -> None:
    feedback = (
        _feedback(
            domain_key="macro",
            specialist_team_key="macro_team",
            resolved_outcome_feedback_count=d("7.000000"),
            correction_follow_through_rate=d("0.876543"),
            memory_age_seconds=d("7654321.123456"),
            calibration_drift=d("0.023457"),
            workload_pressure=d("0.345679"),
        ),
    )
    baseline = _report(feedback)

    with localcontext(Context(prec=7, rounding=ROUND_DOWN)):
        constrained = _report(feedback)

    assert constrained == baseline
    assert constrained.payload == baseline.payload


def test_public_decimal_inputs_require_exact_type_and_six_decimal_places() -> None:
    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="correction_follow_through_rate.*Decimal"):
        _feedback(
            correction_follow_through_rate=DecimalSubclass("0.900000"),
        )
    with pytest.raises(
        ValueError,
        match="correction_follow_through_rate.*six decimal places",
    ):
        _feedback(correction_follow_through_rate=d("0.9000001"))


def test_build_revalidates_frozen_config_input_and_public_payload_item() -> None:
    config = ResearchTeamSpecialistLearningVelocityConfig()
    object.__setattr__(config, "watch_learning_velocity_score", d("0.510000"))
    with pytest.raises(ValueError, match="watch_learning_velocity_score"):
        _report((_feedback(),), config=config)

    feedback = _feedback()
    object.__setattr__(
        feedback,
        "correction_follow_through_rate",
        d("0.800000"),
    )
    with pytest.raises(ValueError, match="correction_follow_through_rate"):
        _report((feedback,))

    public_item = ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
        key="safe_note",
        value="original value",
    )
    object.__setattr__(public_item, "value", "changed value")
    with pytest.raises(ValueError, match="value"):
        _report((_feedback(),), public_payload=(public_item,))


def test_object_setattr_revalidation_preserves_exact_decimal_representation() -> None:
    config = ResearchTeamSpecialistLearningVelocityConfig()
    object.__setattr__(
        config,
        "watch_learning_velocity_score",
        d("0.5000000"),
    )

    with pytest.raises(ValueError, match="watch_learning_velocity_score"):
        _report((_feedback(),), config=config)


def test_payload_rejects_noncanonical_row_order_and_future_observations() -> None:
    report = _report(
        (
            _feedback(domain_key="macro", specialist_team_key="macro_team"),
            _feedback(
                domain_key="crypto",
                specialist_team_key="crypto_team",
                resolved_outcome_feedback_count=d("3.000000"),
                correction_follow_through_rate=d("0.650000"),
                memory_age_seconds=d("1728000.000000"),
                calibration_drift=d("0.070000"),
                workload_pressure=d("0.600000"),
            ),
        ),
    )
    object.__setattr__(report, "rows", tuple(reversed(report.rows)))
    values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    object.__setattr__(
        report,
        "derived_validation_digest",
        api._report_digest_from_values(values),
    )
    with pytest.raises(ValueError, match="rows.*canonical"):
        _ = report.payload

    report = _report((_feedback(),))
    object.__setattr__(report.rows[0], "observed_at", NOW + timedelta(seconds=1))
    values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    object.__setattr__(
        report,
        "derived_validation_digest",
        api._report_digest_from_values(values),
    )
    with pytest.raises(ValueError, match="observed_at.*generated_at"):
        _ = report.payload


def test_payload_revalidates_config_independent_row_derivations() -> None:
    report = _report((_feedback(),))
    object.__setattr__(report.rows[0], "workload_capacity_score", d("0.100000"))
    values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    object.__setattr__(
        report,
        "derived_validation_digest",
        api._report_digest_from_values(values),
    )

    with pytest.raises(ValueError, match="workload_capacity_score"):
        api.research_team_specialist_learning_velocity_report_digest(report)


def test_payload_rejects_resigned_forged_derived_row_scores() -> None:
    report = _report((_feedback(),))
    object.__setattr__(
        report.rows[0],
        "resolved_feedback_depth_score",
        d("0.500000"),
    )
    _resign_report_unsafe(report)
    with pytest.raises(ValueError, match="resolved_feedback_depth_score"):
        _ = report.payload

    report = _report((_feedback(),))
    object.__setattr__(
        report.rows[0],
        "memory_freshness_score",
        d("0.500000"),
    )
    _resign_report_unsafe(report)
    with pytest.raises(ValueError, match="memory_freshness_score"):
        _ = report.payload

    report = _report((_feedback(),))
    object.__setattr__(
        report.rows[0],
        "learning_velocity_score",
        d("0.990000"),
    )
    object.__setattr__(
        report,
        "average_learning_velocity_score",
        d("0.990000"),
    )
    object.__setattr__(report, "min_learning_velocity_score", d("0.990000"))
    _resign_report_unsafe(report)
    with pytest.raises(ValueError, match="learning_velocity_score"):
        _ = report.payload


def test_payload_rejects_resigned_forged_status_reasons_and_matching_counts() -> None:
    report = _report((_feedback(),))
    object.__setattr__(report.rows[0], "velocity_status", "watch")
    object.__setattr__(
        report.rows[0],
        "reason_codes",
        ("learning_velocity_score_watch",),
    )
    object.__setattr__(report, "report_status", "watch")
    object.__setattr__(report, "pass_count", d("0.000000"))
    object.__setattr__(report, "watch_count", d("1.000000"))
    object.__setattr__(
        report,
        "reason_codes",
        ("learning_velocity_score_watch",),
    )
    _resign_report_unsafe(report)

    with pytest.raises(ValueError, match="velocity_status|reason_codes"):
        _ = report.payload


@pytest.mark.parametrize(
    ("target_name", "field_name", "forged_value"),
    (
        ("row", "resolved_feedback_depth_score", d("0.500000")),
        ("row", "memory_freshness_score", d("0.500000")),
        ("row", "calibration_stability_score", d("0.500000")),
        ("row", "workload_capacity_score", d("0.500000")),
        ("row", "learning_velocity_score", d("0.500000")),
        ("row", "velocity_status", "watch"),
        ("row", "reason_codes", ("learning_velocity_score_watch",)),
        ("report", "domain_count", d("2.000000")),
        ("report", "pass_count", d("0.000000")),
        ("report", "watch_count", d("1.000000")),
        ("report", "block_count", d("1.000000")),
        ("report", "average_learning_velocity_score", d("0.500000")),
        ("report", "min_learning_velocity_score", d("0.500000")),
        ("report", "max_workload_pressure", d("0.400000")),
        ("report", "max_memory_age_seconds", d("86401.000000")),
        ("report", "report_status", "watch"),
        ("report", "reason_codes", ("learning_velocity_score_watch",)),
    ),
)
def test_payload_recomputes_every_derived_field_after_resigning(
    target_name: str,
    field_name: str,
    forged_value: object,
) -> None:
    report = _report((_feedback(),))
    target = report.rows[0] if target_name == "row" else report
    object.__setattr__(target, field_name, forged_value)
    _resign_report_unsafe(report)

    with pytest.raises(ValueError, match=field_name):
        _ = report.payload


def test_config_version_pins_the_supported_parameter_profile() -> None:
    with pytest.raises(
        ValueError,
        match="watch_learning_velocity_score.*supported default",
    ):
        ResearchTeamSpecialistLearningVelocityConfig(
            watch_learning_velocity_score=d("0.600000"),
        )

    with pytest.raises(
        ValueError,
        match="resolved_feedback_depth_weight.*supported default",
    ):
        ResearchTeamSpecialistLearningVelocityConfig(
            resolved_feedback_depth_weight=d("0.200000"),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "resolved_outcome_feedback_count",
        "correction_follow_through_rate",
        "memory_age_seconds",
        "calibration_drift",
        "workload_pressure",
    ),
)
def test_feedback_rejects_signed_zero(field_name: str) -> None:
    with pytest.raises(ValueError, match=rf"{field_name}.*signed zero"):
        _feedback(**{field_name: d("-0.000000")})


def test_config_rejects_signed_zero() -> None:
    with pytest.raises(
        ValueError,
        match="watch_learning_velocity_score.*signed zero",
    ):
        ResearchTeamSpecialistLearningVelocityConfig(
            watch_learning_velocity_score=d("-0.000000"),
        )


@pytest.mark.parametrize("value", ("NaN", "Infinity", "-Infinity"))
def test_nonfinite_decimal_inputs_are_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="workload_pressure.*finite"):
        _feedback(workload_pressure=d(value))


@pytest.mark.parametrize(
    "field_name",
    (
        "resolved_outcome_feedback_count",
        "memory_age_seconds",
        "correction_follow_through_rate",
        "calibration_drift",
        "workload_pressure",
    ),
)
def test_oversized_finite_decimal_inputs_are_uniformly_value_errors(
    field_name: str,
) -> None:
    oversized = d(f"{'9' * 1000}.000000")

    with pytest.raises(ValueError):
        _feedback(**{field_name: oversized})


def test_payload_rejects_resigned_signed_zero_after_instance_tampering() -> None:
    report = _report((_feedback(workload_pressure=d("0.000000")),))
    object.__setattr__(
        report.rows[0],
        "workload_pressure",
        d("-0.000000"),
    )
    _resign_report_unsafe(report)

    with pytest.raises(ValueError, match="signed zero"):
        _ = report.payload


def test_private_specialist_team_keys_are_sha256_anonymized_before_storage() -> None:
    private_key = "internal_specialist_17"
    expected_key = f"anon_{hashlib.sha256(private_key.encode('utf-8')).hexdigest()}"

    feedback = _feedback(specialist_team_key=private_key)
    report = _report((feedback,))
    payload_text = json.dumps(report.payload, sort_keys=True)

    assert feedback.specialist_team_key == expected_key
    assert report.rows[0].specialist_team_key == expected_key
    assert expected_key in payload_text
    assert private_key not in payload_text


def test_payload_rejects_resigned_raw_specialist_team_key() -> None:
    private_key = "internal_specialist_17"
    report = _report((_feedback(specialist_team_key=private_key),))
    object.__setattr__(report.rows[0], "specialist_team_key", private_key)
    _resign_report_unsafe(report)

    with pytest.raises(ValueError, match="specialist_team_key.*anonymized"):
        _ = report.payload


@pytest.mark.parametrize("control_character", ("\n", "\r", "\t", "\x00", "\x1f", "\x7f"))
def test_public_strings_reject_newlines_and_control_characters(
    control_character: str,
) -> None:
    with pytest.raises(ValueError):
        _feedback(domain_key=f"macro{control_character}x")
    with pytest.raises(ValueError):
        _feedback(feedback_config_version=f"feedback{control_character}v1")
    with pytest.raises(ValueError, match="control"):
        ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
            key="safe_note",
            value=f"safe{control_character}value",
        )


@pytest.mark.parametrize(
    ("degraded_feedback", "expected_status"),
    (
        (
            _feedback(
                domain_key="watch_domain",
                memory_age_seconds=d("604801.000000"),
            ),
            "watch",
        ),
        (
            _feedback(
                domain_key="block_domain",
                memory_age_seconds=d("8640000.000000"),
            ),
            "block",
        ),
    ),
)
def test_nonpass_reports_filter_row_level_pass_sentinel(
    degraded_feedback: ResearchTeamSpecialistLearningVelocityDomainFeedback,
    expected_status: str,
) -> None:
    report = _report(
        (
            _feedback(domain_key="pass_domain"),
            degraded_feedback,
        ),
    )

    assert report.report_status == expected_status
    assert "specialist_learning_velocity_pass" not in report.reason_codes


def test_empty_report_uses_locked_zero_metrics_and_empty_reason() -> None:
    report = _report(())

    assert report.report_status == "block"
    assert report.domain_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_learning_velocity_score == d("0.000000")
    assert report.min_learning_velocity_score == d("0.000000")
    assert report.max_workload_pressure == d("0.000000")
    assert report.max_memory_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.feedback_config_versions == ()
    assert report.reason_codes == ("specialist_learning_velocity_empty",)
    assert report.reason_code_counts == (
        api.ResearchTeamSpecialistLearningVelocityReasonCodeCount(
            reason_code="specialist_learning_velocity_empty",
            count=d("1.000000"),
        ),
    )
    assert report.payload["rows"] == []


def test_frozen_dataclasses_decimal_only_hard_flags_and_digest_tampering() -> None:
    report = _report(
        (_feedback(),),
        public_payload=(
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                key="safe_note",
                value="learning loop audit",
            ),
        ),
    )

    for value in (
        ResearchTeamSpecialistLearningVelocityConfig(),
        _feedback(),
        report.rows[0],
        report.reason_code_counts[0],
        report.public_payload[0],
        report,
    ):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(ResearchTeamSpecialistLearningVelocityReport):
            pass

    with pytest.raises(ValueError, match="resolved_outcome_feedback_count"):
        _feedback(resolved_outcome_feedback_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="correction_follow_through_rate"):
        _feedback(correction_follow_through_rate=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="workload_pressure"):
        _feedback(workload_pressure=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchTeamSpecialistLearningVelocityConfig(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                    key="safe_note",
                    value="changed value",
                ),
            ),
        )


def test_rejects_unsafe_public_payload_and_public_surfaces() -> None:
    unsafe_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "auth",
        "network",
        "database",
        "sizing",
        "recommendation",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                key=f"{term}_key",
                value="safe value",
            )
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
                key="safe_key",
                value=f"{term} value",
            )

    with pytest.raises(ValueError, match="unsafe public"):
        _feedback(domain_key="market_macro")
    with pytest.raises(ValueError, match="feedback_config_version"):
        _feedback(feedback_config_version=" feedback-v1 ")

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchTeamSpecialistLearningVelocityConfig,
        ResearchTeamSpecialistLearningVelocityDomainFeedback,
        ResearchTeamSpecialistLearningVelocityDomainRow,
        ResearchTeamSpecialistLearningVelocityPublicPayloadItem,
        api.ResearchTeamSpecialistLearningVelocityReasonCodeCount,
        ResearchTeamSpecialistLearningVelocityReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def test_module_ast_has_no_io_network_database_or_dynamic_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    forbidden_import_roots = {
        "aiohttp",
        "hmac",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "Popen",
        "connect",
        "eval",
        "exec",
        "execute",
        "executemany",
        "getenv",
        "open",
        "read",
        "request",
        "run",
        "system",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {*forbidden_call_names, "compile"}
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    assert imported_roots.isdisjoint(forbidden_import_roots)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
