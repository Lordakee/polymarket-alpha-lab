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

    class ConfigSubclass(api.OutcomeResolutionEvidenceReadinessConfig):
        pass

    with pytest.raises(ValueError, match="config must be an OutcomeResolutionEvidenceReadinessConfig"):
        api.build_outcome_resolution_evidence_readiness_report(
            (),
            config=ConfigSubclass(),
        )

    class InputSubclass(api.OutcomeResolutionEvidenceReadinessInput):
        pass

    with pytest.raises(ValueError, match="items must contain OutcomeResolutionEvidenceReadinessInput values"):
        api.build_outcome_resolution_evidence_readiness_report(
            (InputSubclass(
                event_id="event-a",
                outcome_id="yes",
                resolution_source_count=d("3.000000"),
                official_source_count=d("1.000000"),
                conflicting_source_count=d("0.000000"),
                last_checked_age_seconds=d("100.000000"),
                pending_ack=False,
                manual_review_required=False,
                settlement_window_seconds=d("3600.000000"),
            ),),
            config=_config(),
        )


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
