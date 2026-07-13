from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.outcome_resolution_evidence_readiness_report"
SOURCE = Path("src/polymarket_alpha_lab/outcome_resolution_evidence_readiness_report.py")


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module(MODULE_NAME)


def _input(**overrides: object) -> object:
    api = _api()
    values = {
        "event_id": "fed-cut-july-2026",
        "outcome_id": "yes",
        "resolution_source_count": d("3.000000"),
        "official_source_count": d("2.000000"),
        "conflicting_source_count": d("0.000000"),
        "last_checked_age_seconds": d("900.000000"),
        "pending_ack": False,
        "manual_review_required": False,
        "settlement_window_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return api.OutcomeResolutionEvidenceReadinessInput(**values)


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": api.DEFAULT_OUTCOME_RESOLUTION_EVIDENCE_READINESS_REPORT_CONFIG_VERSION,
        "required_resolution_source_count": d("3.000000"),
        "required_official_source_count": d("1.000000"),
        "freshness_warning_ratio": d("0.500000"),
        "freshness_blocker_ratio": d("1.000000"),
    }
    values.update(overrides)
    return api.OutcomeResolutionEvidenceReadinessConfig(**values)


def _report(*items: object, **config_overrides: object) -> object:
    api = _api()
    return api.build_outcome_resolution_evidence_readiness_report(
        items,
        config=_config(**config_overrides),
    )


def test_rolls_up_ready_attention_and_blocker_bands_with_quorum_gap_and_ack_age() -> None:
    report = _report(
        _input(
            event_id="ready-event",
            outcome_id="yes",
            resolution_source_count=d("4.000000"),
            official_source_count=d("2.000000"),
            conflicting_source_count=d("0.000000"),
            last_checked_age_seconds=d("900.000000"),
            pending_ack=False,
            manual_review_required=False,
            settlement_window_seconds=d("3600.000000"),
        ),
        _input(
            event_id="attention-event",
            outcome_id="yes",
            resolution_source_count=d("3.000000"),
            official_source_count=d("1.000000"),
            conflicting_source_count=d("0.000000"),
            last_checked_age_seconds=d("2400.000000"),
            pending_ack=True,
            manual_review_required=False,
            settlement_window_seconds=d("3600.000000"),
        ),
        _input(
            event_id="blocker-event",
            outcome_id="yes",
            resolution_source_count=d("1.000000"),
            official_source_count=d("0.000000"),
            conflicting_source_count=d("1.000000"),
            last_checked_age_seconds=d("4200.000000"),
            pending_ack=True,
            manual_review_required=True,
            settlement_window_seconds=d("3600.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.report_band == "blocker"
    assert report.item_count == d("3.000000")
    assert report.ready_count == d("1.000000")
    assert report.attention_count == d("1.000000")
    assert report.blocker_count == d("1.000000")
    assert report.readiness_ratio == d("0.333333")
    assert report.max_evidence_quorum_gap == d("2.000000")
    assert report.max_pending_ack_age_seconds == d("4200.000000")
    assert report.max_last_checked_age_seconds == d("4200.000000")
    assert report.reason_codes == (
        "outcome_resolution_evidence_readiness_blocker",
        "outcome_resolution_evidence_conflicting_sources",
        "outcome_resolution_evidence_quorum_gap",
        "outcome_resolution_evidence_pending_ack",
        "outcome_resolution_evidence_manual_review_required",
        "outcome_resolution_evidence_stale_check",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.event_id for row in report.rows) == (
        "blocker-event",
        "attention-event",
        "ready-event",
    )

    blocker = report.rows[0]
    assert blocker.band == "blocker"
    assert blocker.evidence_quorum_gap == d("2.000000")
    assert blocker.official_source_gap == d("1.000000")
    assert blocker.pending_ack_age_seconds == d("4200.000000")
    assert blocker.freshness_ratio == d("1.000000")
    assert blocker.reason_codes == (
        "outcome_resolution_evidence_readiness_blocker",
        "outcome_resolution_evidence_conflicting_sources",
        "outcome_resolution_evidence_quorum_gap",
        "outcome_resolution_evidence_pending_ack",
        "outcome_resolution_evidence_manual_review_required",
        "outcome_resolution_evidence_stale_check",
    )

    attention = report.rows[1]
    assert attention.band == "attention"
    assert attention.evidence_quorum_gap == d("0.000000")
    assert attention.pending_ack_age_seconds == d("2400.000000")
    assert attention.freshness_ratio == d("0.666667")
    assert attention.reason_codes == (
        "outcome_resolution_evidence_readiness_attention",
        "outcome_resolution_evidence_pending_ack",
        "outcome_resolution_evidence_stale_check",
    )

    ready = report.rows[2]
    assert ready.band == "ready"
    assert ready.evidence_quorum_gap == d("0.000000")
    assert ready.official_source_gap == d("0.000000")
    assert ready.pending_ack_age_seconds == d("0.000000")
    assert ready.reason_codes == (
        "outcome_resolution_evidence_readiness_ready",
    )


def test_empty_report_is_attention_free_readonly_and_decimal_zeroed() -> None:
    report = _report()

    assert report.report_band == "ready"
    assert report.reason_codes == (
        "outcome_resolution_evidence_readiness_ready",
    )
    assert report.item_count == d("0.000000")
    assert report.ready_count == d("0.000000")
    assert report.attention_count == d("0.000000")
    assert report.blocker_count == d("0.000000")
    assert report.readiness_ratio == d("0.000000")
    assert report.max_evidence_quorum_gap == d("0.000000")
    assert report.max_pending_ack_age_seconds == d("0.000000")
    assert report.max_last_checked_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_readiness_signals_include_clarity_latency_lockup_and_pending_escalation() -> None:
    report = _report(
        _input(
            event_id="latency-event",
            outcome_id="yes",
            resolution_source_count=d("3.000000"),
            official_source_count=d("1.000000"),
            conflicting_source_count=d("0.000000"),
            last_checked_age_seconds=d("1200.000000"),
            pending_ack=False,
            manual_review_required=False,
            settlement_window_seconds=d("3600.000000"),
            resolution_criteria_clarity_score=d("0.750000"),
            oracle_source_latency_seconds=d("5400.000000"),
            settlement_delay_seconds=d("1800.000000"),
            capital_lockup_seconds=d("3600.000000"),
            pending_outcome_age_seconds=d("0.000000"),
        ),
        _input(
            event_id="escalation-event",
            outcome_id="no",
            resolution_source_count=d("3.000000"),
            official_source_count=d("1.000000"),
            conflicting_source_count=d("0.000000"),
            last_checked_age_seconds=d("600.000000"),
            pending_ack=True,
            manual_review_required=False,
            settlement_window_seconds=d("3600.000000"),
            resolution_criteria_clarity_score=d("0.250000"),
            oracle_source_latency_seconds=d("900.000000"),
            settlement_delay_seconds=d("9000.000000"),
            capital_lockup_seconds=d("10800.000000"),
            pending_outcome_age_seconds=d("9600.000000"),
        ),
    )

    assert report.report_band == "blocker"
    assert report.max_oracle_source_latency_seconds == d("5400.000000")
    assert report.max_settlement_delay_seconds == d("9000.000000")
    assert report.max_capital_lockup_seconds == d("10800.000000")
    assert report.max_pending_outcome_age_seconds == d("9600.000000")
    assert report.min_resolution_criteria_clarity_score == d("0.250000")
    assert report.reason_codes == (
        "outcome_resolution_evidence_readiness_blocker",
        "outcome_resolution_criteria_unclear",
        "outcome_resolution_oracle_source_latency",
        "outcome_resolution_settlement_delay_capital_lockup",
        "outcome_resolution_evidence_pending_ack",
        "outcome_resolution_pending_outcome_escalation",
    )

    escalation = report.rows[0]
    assert escalation.event_id == "escalation-event"
    assert escalation.band == "blocker"
    assert escalation.resolution_criteria_clarity_score == d("0.250000")
    assert escalation.oracle_source_latency_seconds == d("900.000000")
    assert escalation.settlement_delay_seconds == d("9000.000000")
    assert escalation.capital_lockup_seconds == d("10800.000000")
    assert escalation.pending_outcome_age_seconds == d("9600.000000")
    assert escalation.reason_codes == (
        "outcome_resolution_evidence_readiness_blocker",
        "outcome_resolution_criteria_unclear",
        "outcome_resolution_settlement_delay_capital_lockup",
        "outcome_resolution_evidence_pending_ack",
        "outcome_resolution_pending_outcome_escalation",
    )

    latency = report.rows[1]
    assert latency.event_id == "latency-event"
    assert latency.band == "attention"
    assert latency.reason_codes == (
        "outcome_resolution_evidence_readiness_attention",
        "outcome_resolution_oracle_source_latency",
    )

    api = _api()
    payload = api.outcome_resolution_evidence_readiness_payload(report)
    assert payload["rows"][0]["capital_lockup_seconds"] == "10800.000000"
    assert payload["max_pending_outcome_age_seconds"] == "9600.000000"


def test_public_payload_digest_is_deterministic_json_ready_and_has_no_live_surface() -> None:
    api = _api()
    first = _report(
        _input(
            event_id="tie-b",
            outcome_id="yes",
            resolution_source_count=d("3.000000"),
            official_source_count=d("1.000000"),
            last_checked_age_seconds=d("600.000000"),
        ),
        _input(
            event_id="tie-a",
            outcome_id="no",
            resolution_source_count=d("3.000000"),
            official_source_count=d("1.000000"),
            last_checked_age_seconds=d("600.000000"),
        ),
    )
    second = _report(*reversed(first.inputs))

    payload = api.outcome_resolution_evidence_readiness_payload(first)
    json.dumps(payload, allow_nan=False, sort_keys=True)
    payload_text = repr(payload).lower()

    assert tuple(row.event_id for row in first.rows) == ("tie-a", "tie-b")
    assert first.public_payload_digest == second.public_payload_digest
    assert payload["public_payload_digest"] == first.public_payload_digest
    assert len(first.public_payload_digest) == 64
    assert set(first.public_payload_digest) <= set("0123456789abcdef")
    assert payload["rows"][0]["resolution_source_count"] == "3.000000"
    assert payload["rows"][0]["freshness_ratio"] == "0.166667"
    assert ".0," not in payload_text
    for forbidden in (
        "wallet",
        "account",
        "private_key",
        "order",
        "recommend",
        "advice",
        "action",
    ):
        assert forbidden not in payload_text


def test_report_digest_sentinels_are_filled_and_forged_digests_cannot_be_output() -> None:
    api = _api()
    report = _report(_input())

    for sentinel in ("", "0" * 64):
        rebuilt = replace(report, public_payload_digest=sentinel)
        assert rebuilt.public_payload_digest == report.public_payload_digest

    with pytest.raises(ValueError, match="public_payload_digest must match"):
        replace(report, public_payload_digest="f" * 64)

    object.__setattr__(report, "public_payload_digest", "e" * 64)
    with pytest.raises(ValueError, match="public_payload_digest must match"):
        api.outcome_resolution_evidence_readiness_payload(report)


def _recompute_outcome_report_digest(report: object) -> None:
    api = _api()
    object.__setattr__(
        report,
        "public_payload_digest",
        api._public_payload_digest(report),
    )


def test_serializer_rejects_row_freshness_tampering_with_recomputed_digest() -> None:
    api = _api()
    report = _report(_input())
    object.__setattr__(report.rows[0], "freshness_ratio", d("0.500000"))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match="freshness_ratio"):
        api.outcome_resolution_evidence_readiness_payload(report)


def test_serializer_rejects_pending_ack_age_tampering_with_recomputed_aggregates() -> None:
    api = _api()
    report = _report(_input())
    object.__setattr__(report.rows[0], "pending_ack_age_seconds", d("1.000000"))
    object.__setattr__(report, "max_pending_ack_age_seconds", d("1.000000"))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match="pending_ack_age_seconds"):
        api.outcome_resolution_evidence_readiness_payload(report)


def test_serializer_rejects_row_band_tampering_with_recomputed_aggregates() -> None:
    api = _api()
    report = _report(_input())
    object.__setattr__(report.rows[0], "band", "attention")
    object.__setattr__(report, "report_band", "attention")
    object.__setattr__(report, "reason_codes", (api.ATTENTION_REASON,))
    object.__setattr__(report, "ready_count", d("0.000000"))
    object.__setattr__(report, "attention_count", d("1.000000"))
    object.__setattr__(report, "readiness_ratio", d("0.000000"))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match="reason_codes"):
        api.outcome_resolution_evidence_readiness_payload(report)


def test_serializer_rejects_row_reason_tampering_with_recomputed_digest() -> None:
    api = _api()
    report = _report(_input())
    object.__setattr__(report.rows[0], "reason_codes", (api.ATTENTION_REASON,))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match="reason_codes"):
        api.outcome_resolution_evidence_readiness_payload(report)


def test_report_persists_effective_config_snapshot_in_public_payload() -> None:
    api = _api()
    config = _config(
        required_resolution_source_count=d("4.000000"),
        freshness_warning_ratio=d("0.400000"),
    )
    report = api.build_outcome_resolution_evidence_readiness_report(
        (_input(),),
        config=config,
    )

    assert report.effective_config == config
    payload = api.outcome_resolution_evidence_readiness_payload(report)
    assert payload["effective_config"]["required_resolution_source_count"] == "4.000000"
    assert payload["effective_config"]["freshness_warning_ratio"] == "0.400000"
    assert payload["effective_config"]["paper_only"] is True
    assert payload["effective_config"]["report_only"] is True
    assert payload["effective_config"]["readonly"] is True


def test_serializer_rejects_coherent_row_band_and_report_rollup_forgery() -> None:
    api = _api()
    report = _report(_input())
    object.__setattr__(report.rows[0], "band", "attention")
    object.__setattr__(report.rows[0], "reason_codes", (api.ATTENTION_REASON,))
    object.__setattr__(report, "report_band", "attention")
    object.__setattr__(report, "reason_codes", (api.ATTENTION_REASON,))
    object.__setattr__(report, "ready_count", d("0.000000"))
    object.__setattr__(report, "attention_count", d("1.000000"))
    object.__setattr__(report, "readiness_ratio", d("0.000000"))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match="band"):
        api.outcome_resolution_evidence_readiness_payload(report)


@pytest.mark.parametrize(
    ("field_name", "tampered_value"),
    (
        ("evidence_quorum_gap", d("1.000000")),
        ("official_source_gap", d("1.000000")),
        (
            "reason_codes",
            (
                "outcome_resolution_evidence_readiness_ready",
                "unrecognized_semantic_reason",
            ),
        ),
    ),
)
def test_serializer_replays_every_row_derivation_from_inputs_and_effective_config(
    field_name: str,
    tampered_value: object,
) -> None:
    api = _api()
    report = _report(_input())
    object.__setattr__(report.rows[0], field_name, tampered_value)
    if field_name in {"evidence_quorum_gap", "official_source_gap"}:
        object.__setattr__(
            report,
            "reason_codes",
            (api.READY_REASON, api.QUORUM_GAP_REASON),
        )
    if field_name == "evidence_quorum_gap":
        object.__setattr__(report, "max_evidence_quorum_gap", d("1.000000"))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match=field_name):
        api.outcome_resolution_evidence_readiness_payload(report)


def test_serializer_rejects_input_row_drift_with_recomputed_digest() -> None:
    api = _api()
    report = _report(_input())
    object.__setattr__(report.inputs[0], "resolution_source_count", d("4.000000"))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match="resolution_source_count"):
        api.outcome_resolution_evidence_readiness_payload(report)


@pytest.mark.parametrize("target_name", ("report", "effective_config", "input", "row"))
@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_serializer_recursively_rejects_rehashed_phase_flag_tampering(
    target_name: str,
    flag_name: str,
) -> None:
    api = _api()
    report = _report(_input())
    targets = {
        "report": report,
        "effective_config": report.effective_config,
        "input": report.inputs[0],
        "row": report.rows[0],
    }
    object.__setattr__(targets[target_name], flag_name, False)
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match=flag_name):
        api.outcome_resolution_evidence_readiness_payload(report)


@pytest.mark.parametrize(
    ("target_name", "field_name"),
    tuple(
        ("effective_config", field_name)
        for field_name in (
            "required_resolution_source_count",
            "required_official_source_count",
            "freshness_warning_ratio",
            "freshness_blocker_ratio",
            "criteria_clarity_warning_score",
            "criteria_clarity_blocker_score",
            "oracle_latency_warning_seconds",
            "oracle_latency_blocker_seconds",
            "settlement_delay_warning_seconds",
            "settlement_delay_blocker_seconds",
            "capital_lockup_warning_seconds",
            "capital_lockup_blocker_seconds",
            "pending_outcome_escalation_seconds",
        )
    )
    + tuple(
        ("input", field_name)
        for field_name in (
            "resolution_source_count",
            "official_source_count",
            "conflicting_source_count",
            "last_checked_age_seconds",
            "settlement_window_seconds",
            "resolution_criteria_clarity_score",
            "oracle_source_latency_seconds",
            "settlement_delay_seconds",
            "capital_lockup_seconds",
            "pending_outcome_age_seconds",
        )
    )
    + tuple(
        ("row", field_name)
        for field_name in (
            "resolution_source_count",
            "official_source_count",
            "conflicting_source_count",
            "evidence_quorum_gap",
            "official_source_gap",
            "last_checked_age_seconds",
            "pending_ack_age_seconds",
            "settlement_window_seconds",
            "freshness_ratio",
            "resolution_criteria_clarity_score",
            "oracle_source_latency_seconds",
            "settlement_delay_seconds",
            "capital_lockup_seconds",
            "pending_outcome_age_seconds",
        )
    )
    + tuple(
        ("report", field_name)
        for field_name in (
            "item_count",
            "ready_count",
            "attention_count",
            "blocker_count",
            "readiness_ratio",
            "max_evidence_quorum_gap",
            "max_pending_ack_age_seconds",
            "max_last_checked_age_seconds",
            "max_oracle_source_latency_seconds",
            "max_settlement_delay_seconds",
            "max_capital_lockup_seconds",
            "max_pending_outcome_age_seconds",
            "min_resolution_criteria_clarity_score",
        )
    ),
)
def test_serializer_recursively_requires_exact_decimal_runtime_types(
    target_name: str,
    field_name: str,
) -> None:
    api = _api()
    report = _report(_input())
    targets = {
        "report": report,
        "effective_config": report.effective_config,
        "input": report.inputs[0],
        "row": report.rows[0],
    }
    value = getattr(targets[target_name], field_name)
    assert type(value) is Decimal
    object.__setattr__(targets[target_name], field_name, int(value))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match=rf"{field_name} must be a Decimal"):
        api.outcome_resolution_evidence_readiness_payload(report)


@pytest.mark.parametrize(
    ("target_name", "field_name", "tampered_value"),
    (
        ("effective_config", "config_version", 1),
        ("input", "event_id", 1),
        ("input", "pending_ack", 0),
        ("row", "band", 1),
        ("row", "reason_codes", ["outcome_resolution_evidence_readiness_ready"]),
        ("row", "pending_ack", 0),
        ("report", "config_version", 1),
    ),
)
def test_serializer_recursively_revalidates_non_decimal_runtime_types(
    target_name: str,
    field_name: str,
    tampered_value: object,
) -> None:
    api = _api()
    report = _report(_input())
    targets = {
        "report": report,
        "effective_config": report.effective_config,
        "input": report.inputs[0],
        "row": report.rows[0],
    }
    object.__setattr__(targets[target_name], field_name, tampered_value)
    _recompute_outcome_report_digest(report)

    with pytest.raises((TypeError, ValueError), match=field_name):
        api.outcome_resolution_evidence_readiness_payload(report)


def test_serializer_requires_exact_input_objects_after_rehash() -> None:
    api = _api()
    report = _report(_input())
    object.__setattr__(report, "inputs", ({"event_id": "forged"},))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match="OutcomeResolutionEvidenceReadinessInput"):
        api.outcome_resolution_evidence_readiness_payload(report)


@pytest.mark.parametrize("collection_name", ("inputs", "rows"))
def test_serializer_rejects_noncanonical_collection_types_after_rehash(
    collection_name: str,
) -> None:
    api = _api()
    report = _report(_input())
    object.__setattr__(report, collection_name, list(getattr(report, collection_name)))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match=rf"{collection_name} must be a tuple"):
        api.outcome_resolution_evidence_readiness_payload(report)


@pytest.mark.parametrize("collection_name", ("inputs", "rows"))
def test_serializer_rejects_noncanonical_collection_order_after_rehash(
    collection_name: str,
) -> None:
    api = _api()
    report = _report(
        _input(event_id="event-a", outcome_id="yes"),
        _input(event_id="event-b", outcome_id="no"),
    )
    object.__setattr__(report, collection_name, tuple(reversed(getattr(report, collection_name))))
    _recompute_outcome_report_digest(report)

    with pytest.raises(ValueError, match=rf"{collection_name} must be in canonical order"):
        api.outcome_resolution_evidence_readiness_payload(report)


@pytest.mark.parametrize(
    "class_name",
    (
        "OutcomeResolutionEvidenceReadinessConfig",
        "OutcomeResolutionEvidenceReadinessInput",
        "OutcomeResolutionEvidenceReadinessRow",
        "OutcomeResolutionEvidenceReadinessReport",
    ),
)
def test_public_dataclasses_reject_subclass_declarations(class_name: str) -> None:
    public_class = getattr(_api(), class_name)

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(f"{class_name}Subclass", (public_class,), {})


def test_dataclasses_reject_floats_bad_counts_false_flags_subclasses_and_mutation() -> None:
    api = _api()

    with pytest.raises(ValueError, match="resolution_source_count must be a Decimal"):
        _input(resolution_source_count=3.0)
    with pytest.raises(ValueError, match="resolution_source_count must be an integer Decimal"):
        _input(resolution_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="official_source_count cannot exceed resolution_source_count"):
        _input(resolution_source_count=d("1.000000"), official_source_count=d("2.000000"))
    with pytest.raises(ValueError, match="conflicting_source_count cannot exceed resolution_source_count"):
        _input(
            resolution_source_count=d("1.000000"),
            official_source_count=d("0.000000"),
            conflicting_source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="pending_ack must be a bool"):
        _input(pending_ack=1)
    with pytest.raises(ValueError, match="settlement_window_seconds must be positive"):
        _input(settlement_window_seconds=d("0.000000"))

    item = _input()
    with pytest.raises(FrozenInstanceError):
        item.event_id = "other-event"
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)

def test_public_numeric_annotations_are_decimal_and_module_scope_is_side_effect_free() -> None:
    api = _api()
    numeric_fragments = (
        "count",
        "ratio",
        "seconds",
        "age",
        "gap",
    )

    for cls_name in (
        "OutcomeResolutionEvidenceReadinessConfig",
        "OutcomeResolutionEvidenceReadinessInput",
        "OutcomeResolutionEvidenceReadinessRow",
        "OutcomeResolutionEvidenceReadinessReport",
    ):
        cls = getattr(api, cls_name)
        assert is_dataclass(cls)
        assert getattr(cls, "__dataclass_params__").frozen is True
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if any(fragment in field.name for fragment in numeric_fragments):
                assert hints[field.name] is Decimal, (
                    cls_name,
                    field.name,
                    hints[field.name],
                )

    text = SOURCE.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden_text = (
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "private_key",
        "wallet",
        "account",
        "recommend",
        "advice",
        "action",
        "open(",
        "print(",
    )
    for token in forbidden_text:
        assert token not in lowered, token

    allowed_import_prefixes = (
        "from __future__",
        "from dataclasses",
        "from decimal",
        "from hashlib",
        "from json",
        "from typing",
        "from polymarket_alpha_lab.team_paper_guard",
    )
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert any(stripped.startswith(prefix) for prefix in allowed_import_prefixes), stripped

    tree = ast.parse(text)
    forbidden_calls = {"open", "print", "exec", "eval", "compile"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls

    assert importlib.util.find_spec(MODULE_NAME) is not None
    for name, value in inspect.getmembers(api):
        if name.startswith("_"):
            continue
        assert not isinstance(value, float), name
