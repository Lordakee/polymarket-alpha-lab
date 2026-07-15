from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "probability_event_manual_blocker_resolution_checklist_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "probability_event_manual_blocker_resolution_checklist_report.py",
)
BLOCKER_REASON_CODES = (
    "source_stale_block",
    "cost_threshold_block",
    "memory_policy_block",
)
REQUIRED_RESOLUTION_ITEMS = (
    "owner_assigned",
    "resolution_note",
    "source_refresh",
    "cost_recheck",
    "memory_policy_recheck",
)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def checklist(**overrides: object) -> Any:
    module = api()
    values = {
        "blocker_reason_codes": BLOCKER_REASON_CODES,
        "owner_assigned": True,
        "resolution_note_present": True,
        "source_refreshed": True,
        "cost_rechecked": True,
        "memory_policy_rechecked": True,
    }
    values.update(overrides)
    return module.build_probability_event_manual_blocker_resolution_checklist_report(
        **values,
    )


def assert_no_json_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_json_numbers(nested)
        return
    if isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_json_numbers(nested)
        return
    assert isinstance(value, bool) or not isinstance(value, (int, float, Decimal))


def test_complete_resolution_checklist_is_resolved_and_readonly() -> None:
    module = api()
    report = checklist()

    assert report.resolution_checklist_status == "resolved"
    assert report.missing_resolution_items == ()
    assert report.manual_next_step == (
        "manual_blocker_resolution_checklist_complete_continue_readonly_review"
    )
    assert report.blocker_reason_codes == BLOCKER_REASON_CODES
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = (
        module.probability_event_manual_blocker_resolution_checklist_report_payload(
            report,
        )
    )
    assert payload == {
        "blocker_reason_codes": list(BLOCKER_REASON_CODES),
        "resolution_checklist_status": "resolved",
        "missing_resolution_items": [],
        "manual_next_step": (
            "manual_blocker_resolution_checklist_complete_continue_readonly_review"
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_json_numbers(payload)


def test_missing_items_are_reported_in_canonical_order() -> None:
    report = checklist(
        owner_assigned=False,
        resolution_note_present=False,
        source_refreshed=False,
        cost_rechecked=False,
        memory_policy_rechecked=False,
    )

    assert report.resolution_checklist_status == "blocked"
    assert report.missing_resolution_items == REQUIRED_RESOLUTION_ITEMS
    assert report.manual_next_step == (
        "assign_owner_and_complete_manual_blocker_resolution_items_before_review"
    )


def test_no_blocker_reason_codes_requires_manual_blocker_context() -> None:
    report = checklist(blocker_reason_codes=())

    assert report.resolution_checklist_status == "blocked"
    assert report.missing_resolution_items == ("blocker_reason_codes",)
    assert report.manual_next_step == (
        "capture_manual_blocker_reason_codes_before_resolution_review"
    )


def test_dataclass_is_frozen_and_hard_flags_are_enforced() -> None:
    report = checklist()

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    for field in fields(report):
        value = getattr(report, field.name)
        if isinstance(value, Decimal):
            assert type(value) is Decimal, field.name
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(
            api().ProbabilityEventManualBlockerResolutionChecklistReport,
        ):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_validation_rejects_noncanonical_inputs() -> None:
    with pytest.raises(ValueError, match="blocker_reason_codes must be an iterable"):
        checklist(blocker_reason_codes="source_stale_block")
    with pytest.raises(ValueError, match="blocker_reason_codes must contain text"):
        checklist(blocker_reason_codes=(object(),))
    with pytest.raises(ValueError, match="blocker_reason_codes must be canonical"):
        checklist(blocker_reason_codes=(" source_stale_block",))
    with pytest.raises(ValueError, match="owner_assigned must be a bool"):
        checklist(owner_assigned=1)
    with pytest.raises(ValueError, match="resolution_note_present must be a bool"):
        checklist(resolution_note_present=None)


def test_module_exposes_no_execution_or_persistence_surfaces() -> None:
    module = api()
    forbidden_fragments = (
        "auth",
        "database",
        "dsn",
        "execute",
        "execution",
        "live",
        "order",
        "persist",
        "private",
        "submit",
        "token",
        "trade",
        "trading",
        "wallet",
    )

    public_names = [name for name in dir(module) if not name.startswith("_")]
    offenders = [
        name
        for name in public_names
        if any(fragment in name.lower() for fragment in forbidden_fragments)
    ]
    assert offenders == []
    assert not any(
        fragment in MODULE_PATH.read_text(encoding="utf-8").lower()
        for fragment in forbidden_fragments
    )
