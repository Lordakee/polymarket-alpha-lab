from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.post_settlement_calibration_experience_feedback_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "post_settlement_calibration_experience_feedback_report.py"
)
GENERATED_AT = datetime(2026, 7, 12, 10, 45, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class AlwaysEqualString(str):
    __hash__ = str.__hash__

    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def settled_event(
    event_key: str = "settled_alpha",
    domain_team: str = "macro",
    *,
    forecast_probability: Decimal = d("0.720000"),
    settled_outcome_probability: Decimal = d("1.000000"),
    baseline_team_calibration_error: Decimal = d("0.040000"),
    settled_team_calibration_error: Decimal = d("0.080000"),
    evidence_readiness_score: Decimal = d("0.900000"),
    retrospective_learning_pressure: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return api().PostSettlementCalibrationExperienceEvent(
        event_key=event_key,
        domain_team=domain_team,
        forecast_probability=forecast_probability,
        settled_outcome_probability=settled_outcome_probability,
        baseline_team_calibration_error=baseline_team_calibration_error,
        settled_team_calibration_error=settled_team_calibration_error,
        evidence_readiness_score=evidence_readiness_score,
        retrospective_learning_pressure=retrospective_learning_pressure,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*events: Any, generated_at: datetime = GENERATED_AT) -> Any:
    return api().build_post_settlement_calibration_experience_feedback_report(
        events,
        generated_at=generated_at,
        config=api().PostSettlementCalibrationExperienceConfig(),
    )


def test_report_records_prediction_residuals_team_drift_and_memory_queue() -> None:
    module = api()
    pass_event = settled_event(
        "settled_pass",
        "macro",
        forecast_probability=d("0.940000"),
        settled_outcome_probability=d("1.000000"),
        baseline_team_calibration_error=d("0.040000"),
        settled_team_calibration_error=d("0.050000"),
        evidence_readiness_score=d("0.920000"),
        retrospective_learning_pressure=d("0.050000"),
    )
    watch_event = settled_event(
        "settled_watch",
        "sports",
        forecast_probability=d("0.620000"),
        settled_outcome_probability=d("1.000000"),
        baseline_team_calibration_error=d("0.050000"),
        settled_team_calibration_error=d("0.130000"),
        evidence_readiness_score=d("0.610000"),
        retrospective_learning_pressure=d("0.300000"),
    )
    block_event = settled_event(
        "settled_block",
        "crypto",
        forecast_probability=d("0.840000"),
        settled_outcome_probability=d("0.000000"),
        baseline_team_calibration_error=d("0.020000"),
        settled_team_calibration_error=d("0.240000"),
        evidence_readiness_score=d("0.350000"),
        retrospective_learning_pressure=d("0.780000"),
    )

    report = build_report(pass_event, watch_event, block_event)
    reversed_report = build_report(block_event, watch_event, pass_event)

    assert is_dataclass(report)
    assert module.POST_SETTLEMENT_CALIBRATION_EXPERIENCE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.event_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.memory_writeback_queue_count == d("2.000000")
    assert report.average_prediction_residual_probability == d("0.426667")
    assert report.average_team_calibration_drift == d("0.103333")
    assert report.max_prediction_residual_probability == d("0.840000")
    assert report.max_team_calibration_drift == d("0.220000")

    blocked, watched, passed = report.rows
    assert [row.event_key for row in report.rows] == [
        "settled_block",
        "settled_watch",
        "settled_pass",
    ]
    assert (blocked.status, watched.status, passed.status) == (
        "block",
        "watch",
        "pass",
    )
    assert blocked.prediction_residual_probability == d("0.840000")
    assert blocked.team_calibration_drift == d("0.220000")
    assert blocked.long_term_memory_writeback_required is True
    assert blocked.manual_next_step == "open_manual_post_settlement_calibration_packet"
    assert blocked.reason_codes == (
        "evidence_readiness_below_block_threshold",
        "prediction_residual_above_block_threshold",
        "retrospective_learning_pressure_block",
        "team_calibration_drift_above_block_threshold",
    )
    assert watched.reason_codes == (
        "evidence_readiness_below_pass_threshold",
        "prediction_residual_above_watch_threshold",
        "retrospective_learning_pressure_watch",
        "team_calibration_drift_above_watch_threshold",
    )
    assert passed.reason_codes == ("post_settlement_calibration_evidence_ready",)

    assert [item.event_key for item in report.memory_writeback_queue] == [
        "settled_block",
        "settled_watch",
    ]
    assert [item.queue_priority for item in report.memory_writeback_queue] == [
        "high",
        "medium",
    ]
    assert report.memory_writeback_queue[0].reason_codes == blocked.reason_codes
    assert all(item.paper_only and item.report_only and item.readonly for item in report.memory_writeback_queue)
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report == reversed_report


def test_memory_queue_sorts_by_public_priority_before_risk_metrics() -> None:
    module = api()
    medium_watch = settled_event(
        "medium_watch",
        forecast_probability=d("0.510000"),
        settled_outcome_probability=d("1.000000"),
        baseline_team_calibration_error=d("0.040000"),
        settled_team_calibration_error=d("0.040000"),
        evidence_readiness_score=d("0.900000"),
        retrospective_learning_pressure=d("0.100000"),
    )
    high_block = settled_event(
        "high_block",
        forecast_probability=d("0.990000"),
        settled_outcome_probability=d("1.000000"),
        baseline_team_calibration_error=d("0.040000"),
        settled_team_calibration_error=d("0.040000"),
        evidence_readiness_score=d("0.400000"),
        retrospective_learning_pressure=d("0.100000"),
    )

    report = build_report(medium_watch, high_block)
    reversed_report = build_report(high_block, medium_watch)

    assert [row.event_key for row in report.rows] == ["medium_watch", "high_block"]
    assert [item.event_key for item in report.memory_writeback_queue] == [
        "high_block",
        "medium_watch",
    ]
    assert [item.queue_priority for item in report.memory_writeback_queue] == [
        "high",
        "medium",
    ]
    assert report == reversed_report

    replayed_payload = (
        module.validate_post_settlement_calibration_experience_feedback_public_payload(
            json.loads(json.dumps(report.payload)),
        )
    )
    assert [
        item["event_key"] for item in replayed_payload["memory_writeback_queue"]
    ] == ["high_block", "medium_watch"]


def test_empty_report_is_readonly_decimal_only_and_requires_manual_collection() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_POST_SETTLEMENT_CALIBRATION_EXPERIENCE_CONFIG_VERSION",
        "POST_SETTLEMENT_CALIBRATION_EXPERIENCE_STATUSES",
        "PostSettlementCalibrationExperienceConfig",
        "PostSettlementCalibrationExperienceEvent",
        "PostSettlementCalibrationExperienceRow",
        "PostSettlementCalibrationExperienceMemoryQueueItem",
        "PostSettlementCalibrationExperienceReasonCodeCount",
        "PostSettlementCalibrationExperienceReport",
        "build_post_settlement_calibration_experience_feedback_report",
        "post_settlement_calibration_experience_feedback_report_digest",
        "post_settlement_calibration_experience_feedback_report_payload",
        "validate_post_settlement_calibration_experience_feedback_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    report = build_report()

    assert report.status == "block"
    assert report.event_count == d("0.000000")
    assert report.memory_writeback_queue_count == d("0.000000")
    assert report.average_prediction_residual_probability == d("0.000000")
    assert report.average_team_calibration_drift == d("0.000000")
    assert report.reason_codes == ("no_settled_calibration_events",)
    assert report.reason_code_counts == (
        module.PostSettlementCalibrationExperienceReasonCodeCount(
            reason_code="no_settled_calibration_events",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    assert report.memory_writeback_queue == ()
    assert report.manual_next_step == "manual_collect_settled_calibration_evidence"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_public_safe_deterministic_and_decimal_string_encoded() -> None:
    module = api()
    report = build_report(
        settled_event("settled_watch", "sports"),
        settled_event(
            "settled_block",
            "crypto",
            forecast_probability=d("0.840000"),
            settled_outcome_probability=d("0.000000"),
            baseline_team_calibration_error=d("0.020000"),
            settled_team_calibration_error=d("0.240000"),
            evidence_readiness_score=d("0.350000"),
            retrospective_learning_pressure=d("0.780000"),
        ),
    )

    payload = module.post_settlement_calibration_experience_feedback_report_payload(report)

    assert payload == report.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-12T10:45:00+00:00"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["rows"][0]["prediction_residual_probability"] == "0.840000"
    assert payload["rows"][0]["team_calibration_drift"] == "0.220000"
    assert payload["memory_writeback_queue"][0]["queue_priority"] == "high"
    assert _float_or_int_paths(payload) == ()
    assert _forbidden_public_fragments(payload) == ()
    assert module.validate_post_settlement_calibration_experience_feedback_public_payload(
        payload,
    ) == payload
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["event_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_post_settlement_calibration_experience_feedback_public_payload(
            tampered,
        )


def test_public_digest_revalidates_and_rejects_tampered_stored_digest() -> None:
    module = api()
    report = build_report(settled_event())
    expected_digest = report.derived_validation_digest

    assert (
        module.post_settlement_calibration_experience_feedback_report_digest(report)
        == expected_digest
    )

    object.__setattr__(report, "derived_validation_digest", "0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.post_settlement_calibration_experience_feedback_report_digest(report)


def test_mapping_payload_materializes_exact_report_and_rejects_rehashed_derived_tampering() -> None:
    module = api()
    report = build_report(
        settled_event("settled_watch", "sports"),
        settled_event(
            "settled_block",
            "crypto",
            forecast_probability=d("0.840000"),
            settled_outcome_probability=d("0.000000"),
            baseline_team_calibration_error=d("0.020000"),
            settled_team_calibration_error=d("0.240000"),
            evidence_readiness_score=d("0.350000"),
            retrospective_learning_pressure=d("0.780000"),
        ),
    )
    payload = json.loads(json.dumps(report.payload))

    assert module.post_settlement_calibration_experience_feedback_report_payload(
        MappingProxyType(payload),
    ) == payload

    mutations: tuple[tuple[tuple[str | int, ...], object], ...] = (
        (("event_count",), "3.000000"),
        (("status",), "watch"),
        (("reason_codes",), ["post_settlement_calibration_evidence_ready"]),
        (("manual_next_step",), "queue_long_term_memory_experience_review"),
        (("rows", 0, "status"), "watch"),
        (
            ("rows", 0, "reason_codes"),
            ["post_settlement_calibration_evidence_ready"],
        ),
        (("rows", 0, "manual_next_step"), "queue_long_term_memory_experience_review"),
    )
    for path, replacement in mutations:
        tampered = json.loads(json.dumps(payload))
        target: Any = tampered
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = replacement
        tampered["derived_validation_digest"] = canonical_digest(tampered)
        with pytest.raises(ValueError):
            module.validate_post_settlement_calibration_experience_feedback_public_payload(
                tampered,
            )

    noncanonical = json.loads(json.dumps(payload))
    noncanonical["event_count"] = "2.0"
    noncanonical["derived_validation_digest"] = canonical_digest(noncanonical)
    with pytest.raises(ValueError):
        module.validate_post_settlement_calibration_experience_feedback_public_payload(
            noncanonical,
        )

    extra_field = json.loads(json.dumps(payload))
    extra_field["note"] = "readonly_calibration_snapshot"
    extra_field["derived_validation_digest"] = canonical_digest(extra_field)
    with pytest.raises(ValueError):
        module.validate_post_settlement_calibration_experience_feedback_public_payload(
            extra_field,
        )


def test_mapping_payload_rejects_string_subclass_with_custom_equality() -> None:
    module = api()
    payload = json.loads(json.dumps(build_report(settled_event()).payload))
    payload["status"] = AlwaysEqualString("unsupported_status")
    payload["derived_validation_digest"] = canonical_digest(payload)

    with pytest.raises(ValueError, match="exact string"):
        module.post_settlement_calibration_experience_feedback_report_payload(
            MappingProxyType(payload),
        )
    with pytest.raises(ValueError, match="exact string"):
        module.validate_post_settlement_calibration_experience_feedback_public_payload(
            payload,
        )


@pytest.mark.parametrize("as_mapping_proxy", (False, True), ids=("mapping", "mapping_proxy"))
@pytest.mark.parametrize(
    "invalid_value_kind",
    (
        "decimal",
        "decimal_subclass",
        "rows_tuple",
        "nested_dataclass",
        "nested_mapping_proxy",
    ),
)
def test_mapping_payload_rejects_non_exact_json_types_before_canonicalization(
    monkeypatch: pytest.MonkeyPatch,
    as_mapping_proxy: bool,
    invalid_value_kind: str,
) -> None:
    module = api()
    report = build_report(settled_event())
    payload = json.loads(json.dumps(report.payload))

    if invalid_value_kind == "decimal":
        payload["event_count"] = Decimal(payload["event_count"])
    elif invalid_value_kind == "decimal_subclass":
        payload["event_count"] = DecimalSubclass(payload["event_count"])
    elif invalid_value_kind == "rows_tuple":
        payload["rows"] = tuple(payload["rows"])
    elif invalid_value_kind == "nested_dataclass":
        payload["rows"][0] = report.rows[0]
    else:
        payload["effective_config"] = MappingProxyType(payload["effective_config"])

    source = MappingProxyType(payload) if as_mapping_proxy else payload

    def fail_if_canonicalized(value: object) -> object:
        raise AssertionError(f"invalid source reached _public_json: {value!r}")

    monkeypatch.setattr(module, "_public_json", fail_if_canonicalized)

    with pytest.raises(ValueError, match="exact JSON types|numeric values"):
        module.post_settlement_calibration_experience_feedback_report_payload(source)


def test_report_retains_all_effective_config_thresholds_for_replay() -> None:
    module = api()
    config = module.PostSettlementCalibrationExperienceConfig(
        prediction_residual_watch_threshold=d("0.300000"),
        prediction_residual_block_threshold=d("0.900000"),
        team_calibration_drift_watch_threshold=d("0.100000"),
        team_calibration_drift_block_threshold=d("0.300000"),
        evidence_readiness_pass_threshold=d("0.850000"),
        evidence_readiness_block_threshold=d("0.400000"),
        retrospective_learning_pressure_watch_threshold=d("0.200000"),
        retrospective_learning_pressure_block_threshold=d("0.800000"),
    )
    report = module.build_post_settlement_calibration_experience_feedback_report(
        (settled_event(),),
        generated_at=GENERATED_AT,
        config=config,
    )

    assert report.status == "pass"
    assert report.effective_config == config
    assert report.effective_config is not config
    assert report.payload["effective_config"] == {
        "config_version": module.DEFAULT_POST_SETTLEMENT_CALIBRATION_EXPERIENCE_CONFIG_VERSION,
        "prediction_residual_watch_threshold": "0.300000",
        "prediction_residual_block_threshold": "0.900000",
        "team_calibration_drift_watch_threshold": "0.100000",
        "team_calibration_drift_block_threshold": "0.300000",
        "evidence_readiness_pass_threshold": "0.850000",
        "evidence_readiness_block_threshold": "0.400000",
        "retrospective_learning_pressure_watch_threshold": "0.200000",
        "retrospective_learning_pressure_block_threshold": "0.800000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    original_payload = report.payload
    original_digest = report.derived_validation_digest
    object.__setattr__(
        config,
        "prediction_residual_watch_threshold",
        d("0.100000"),
    )

    assert report.effective_config.prediction_residual_watch_threshold == d("0.300000")
    assert report.payload == original_payload
    assert (
        module.post_settlement_calibration_experience_feedback_report_digest(report)
        == original_digest
    )


def test_rehashed_payload_rejects_coordinated_status_and_queue_reclassification() -> None:
    module = api()
    report = build_report(
        settled_event(
            forecast_probability=d("0.940000"),
            baseline_team_calibration_error=d("0.040000"),
            settled_team_calibration_error=d("0.050000"),
            evidence_readiness_score=d("0.920000"),
            retrospective_learning_pressure=d("0.050000"),
        ),
    )
    payload = json.loads(json.dumps(report.payload))
    reason = "retrospective_learning_pressure_watch"
    row = payload["rows"][0]
    row["long_term_memory_writeback_required"] = True
    row["status"] = "watch"
    row["reason_codes"] = [reason]
    row["manual_next_step"] = "queue_long_term_memory_experience_review"
    payload["pass_count"] = "0.000000"
    payload["watch_count"] = "1.000000"
    payload["block_count"] = "0.000000"
    payload["memory_writeback_queue_count"] = "1.000000"
    payload["status"] = "watch"
    payload["reason_codes"] = [reason]
    payload["reason_code_counts"] = [
        {
            "reason_code": reason,
            "count": "1.000000",
            "row_ratio": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    payload["manual_next_step"] = "queue_long_term_memory_experience_review"
    payload["memory_writeback_queue"] = [
        {
            "event_key": row["event_key"],
            "domain_team": row["domain_team"],
            "prediction_residual_probability": row[
                "prediction_residual_probability"
            ],
            "team_calibration_drift": row["team_calibration_drift"],
            "evidence_readiness_score": row["evidence_readiness_score"],
            "retrospective_learning_pressure": row[
                "retrospective_learning_pressure"
            ],
            "queue_priority": "medium",
            "reason_codes": [reason],
            "manual_next_step": "queue_long_term_memory_experience_review",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    payload["derived_validation_digest"] = canonical_digest(payload)

    with pytest.raises(ValueError, match="reason_codes"):
        module.validate_post_settlement_calibration_experience_feedback_public_payload(
            payload,
        )


def test_builder_rejects_duplicate_event_keys() -> None:
    duplicate = settled_event(
        forecast_probability=d("0.940000"),
        baseline_team_calibration_error=d("0.040000"),
        settled_team_calibration_error=d("0.050000"),
    )

    with pytest.raises(ValueError, match="event_key.*unique"):
        build_report(duplicate, duplicate)


def test_mapping_payload_rejects_duplicate_event_keys_after_rehash() -> None:
    module = api()
    report = build_report(
        settled_event(
            forecast_probability=d("0.940000"),
            baseline_team_calibration_error=d("0.040000"),
            settled_team_calibration_error=d("0.050000"),
        ),
    )
    payload = json.loads(json.dumps(report.payload))
    payload["rows"].append(json.loads(json.dumps(payload["rows"][0])))
    payload["event_count"] = "2.000000"
    payload["pass_count"] = "2.000000"
    payload["reason_code_counts"][0]["count"] = "2.000000"
    payload["derived_validation_digest"] = canonical_digest(payload)

    with pytest.raises(ValueError, match="event_key.*unique"):
        module.validate_post_settlement_calibration_experience_feedback_public_payload(
            payload,
        )


def test_public_digest_and_payload_reject_duplicate_event_keys() -> None:
    module = api()
    report = build_report(
        settled_event(
            forecast_probability=d("0.940000"),
            baseline_team_calibration_error=d("0.040000"),
            settled_team_calibration_error=d("0.050000"),
        ),
    )
    row = report.rows[0]
    duplicate_reason_count = module.PostSettlementCalibrationExperienceReasonCodeCount(
        reason_code=report.reason_code_counts[0].reason_code,
        count=d("2.000000"),
        row_ratio=d("1.000000"),
    )
    object.__setattr__(report, "rows", (row, row))
    object.__setattr__(report, "event_count", d("2.000000"))
    object.__setattr__(report, "pass_count", d("2.000000"))
    object.__setattr__(report, "reason_code_counts", (duplicate_reason_count,))

    with pytest.raises(ValueError, match="event_key.*unique"):
        module.post_settlement_calibration_experience_feedback_report_digest(report)
    with pytest.raises(ValueError, match="event_key.*unique"):
        module.post_settlement_calibration_experience_feedback_report_payload(report)


def test_public_digest_and_payload_revalidate_nested_rows() -> None:
    module = api()
    report = build_report(
        settled_event(
            forecast_probability=d("0.940000"),
            baseline_team_calibration_error=d("0.040000"),
            settled_team_calibration_error=d("0.050000"),
        ),
    )
    object.__setattr__(
        report.rows[0],
        "manual_next_step",
        "queue_long_term_memory_experience_review",
    )

    with pytest.raises(ValueError, match="manual_next_step"):
        module.post_settlement_calibration_experience_feedback_report_digest(report)
    with pytest.raises(ValueError, match="manual_next_step"):
        module.post_settlement_calibration_experience_feedback_report_payload(report)


def test_object_payload_rejects_report_count_decimal_subclass() -> None:
    module = api()
    report = build_report(settled_event())
    object.__setattr__(report, "event_count", DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="event_count must be an exact Decimal"):
        module.post_settlement_calibration_experience_feedback_report_payload(report)


def test_object_payload_rejects_nested_row_decimal_subclass() -> None:
    module = api()
    report = build_report(settled_event())
    object.__setattr__(
        report.rows[0],
        "forecast_probability",
        DecimalSubclass(str(report.rows[0].forecast_probability)),
    )

    with pytest.raises(ValueError, match="forecast_probability must be an exact Decimal"):
        module.post_settlement_calibration_experience_feedback_report_payload(report)


def test_validation_rejects_non_decimal_inputs_flags_and_mutation() -> None:
    module = api()
    report = build_report(settled_event())

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclass"):
        class Child(module.PostSettlementCalibrationExperienceEvent):
            pass

    with pytest.raises(ValueError, match="Decimal"):
        settled_event(forecast_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        settled_event(settled_team_calibration_error=DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="probability"):
        settled_event(settled_outcome_probability=d("0.500000"))
    with pytest.raises(ValueError, match="ratio"):
        settled_event(evidence_readiness_score=d("1.100000"))
    with pytest.raises(ValueError, match="event_key"):
        settled_event(event_key="market_slug")
    with pytest.raises(ValueError, match="domain_team"):
        settled_event(domain_team="Macro Team")
    with pytest.raises(ValueError, match="paper_only"):
        settled_event(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_source_file_has_no_persistence_network_or_execution_surface() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden = ("persist", "database", "scrap", "supabase", "auth", "wallet", "order")

    assert "open(" not in source
    assert "Path(" not in source
    assert "requests" not in source
    assert "httpx" not in source
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = " ".join(alias.name for alias in node.names)
            assert not any(term in imported.lower() for term in forbidden)
        elif isinstance(node, ast.Name):
            assert not any(term in node.id.lower() for term in forbidden)
        elif isinstance(node, ast.Attribute):
            assert not any(term in node.attr.lower() for term in forbidden)


def _float_or_int_paths(value: Any, path: str = "$") -> tuple[str, ...]:
    if type(value) in (int, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item_value in value.items():
            paths.extend(_float_or_int_paths(item_value, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item_value in enumerate(value):
            paths.extend(_float_or_int_paths(item_value, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _forbidden_public_fragments(value: Any) -> tuple[str, ...]:
    forbidden = ("persist", "database", "scrap", "supabase", "auth", "wallet", "order")
    encoded = json.dumps(value, sort_keys=True).lower()
    return tuple(term for term in forbidden if term in encoded)
