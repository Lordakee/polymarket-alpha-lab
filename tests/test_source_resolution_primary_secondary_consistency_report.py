from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.source_resolution_primary_secondary_consistency_report import (
    SourceResolutionPrimarySecondaryConsistencyInput,
    SourceResolutionPrimarySecondaryConsistencyReport,
    build_source_resolution_primary_secondary_consistency_report,
    source_resolution_primary_secondary_consistency_report_payload,
    validate_source_resolution_primary_secondary_consistency_public_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def item(**overrides: object) -> SourceResolutionPrimarySecondaryConsistencyInput:
    values = {
        "primary_source_present": True,
        "secondary_source_count": d("2"),
        "consistent_secondary_count": d("2"),
        "conflicting_secondary_count": d("0"),
        "freshness_gap_hours": d("1.250000"),
    }
    values.update(overrides)
    return SourceResolutionPrimarySecondaryConsistencyInput(**values)


def report(
    source_item: SourceResolutionPrimarySecondaryConsistencyInput,
) -> SourceResolutionPrimarySecondaryConsistencyReport:
    return build_source_resolution_primary_secondary_consistency_report(source_item)


def test_primary_present_with_consistent_secondaries_passes() -> None:
    consistency_report = report(item())

    assert type(consistency_report) is SourceResolutionPrimarySecondaryConsistencyReport
    assert consistency_report.consistency_status == "consistent"
    assert consistency_report.primary_source_present is True
    assert consistency_report.secondary_source_count == d("2")
    assert consistency_report.consistent_secondary_count == d("2")
    assert consistency_report.conflicting_secondary_count == d("0")
    assert consistency_report.freshness_gap_hours == d("1.250000")
    assert consistency_report.reason_codes == (
        "primary_secondary_resolution_consistent",
    )
    assert consistency_report.manual_next_step == "no_manual_action_required"
    assert consistency_report.paper_only is True
    assert consistency_report.report_only is True
    assert consistency_report.readonly is True


def test_missing_primary_blocks_and_requests_primary_source_review() -> None:
    consistency_report = report(
        item(
            primary_source_present=False,
            secondary_source_count=d("3"),
            consistent_secondary_count=d("3"),
            conflicting_secondary_count=d("0"),
        ),
    )

    assert consistency_report.consistency_status == "blocked"
    assert consistency_report.reason_codes == ("primary_source_missing",)
    assert consistency_report.manual_next_step == "attach_primary_resolution_source"


def test_secondary_conflicts_block_before_freshness_watch() -> None:
    consistency_report = report(
        item(
            secondary_source_count=d("3"),
            consistent_secondary_count=d("1"),
            conflicting_secondary_count=d("2"),
            freshness_gap_hours=d("30.000000"),
        ),
    )

    assert consistency_report.consistency_status == "blocked"
    assert consistency_report.reason_codes == (
        "secondary_source_conflict",
        "secondary_consistency_quorum_gap",
        "freshness_gap_watch",
    )
    assert consistency_report.manual_next_step == "manual_adjudicate_conflicting_sources"


def test_missing_secondary_and_stale_gap_watch_without_conflicts() -> None:
    consistency_report = report(
        item(
            secondary_source_count=d("0"),
            consistent_secondary_count=d("0"),
            freshness_gap_hours=d("24.000000"),
        ),
    )

    assert consistency_report.consistency_status == "watch"
    assert consistency_report.reason_codes == (
        "secondary_source_missing",
        "freshness_gap_watch",
    )
    assert consistency_report.manual_next_step == "collect_secondary_resolution_source"


def test_payload_is_public_safe_decimal_only_and_digest_validated() -> None:
    consistency_report = report(item())
    payload = source_resolution_primary_secondary_consistency_report_payload(
        consistency_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["primary_source_present"] is True
    assert payload["secondary_source_count"] == "2"
    assert payload["freshness_gap_hours"] == "1.250000"
    assert payload["public_payload"] == {
        "consistency_status": "consistent",
        "reason_codes": ["primary_secondary_resolution_consistent"],
        "manual_next_step": "no_manual_action_required",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert len(payload["payload_digest"]) == 64
    assert validate_source_resolution_primary_secondary_consistency_public_payload(
        payload,
    ) is True
    assert not any(
        isinstance(value, float | int) and type(value) is not bool
        for value in _walk_payload_values(payload)
    )
    assert all(
        forbidden not in encoded.lower()
        for forbidden in (
            "http://",
            "https://",
            "wallet",
            "key",
            "signing",
            "execution",
            "trade",
            "order",
        )
    )


def test_validation_rejects_bad_types_counts_flags_and_inconsistent_counts() -> None:
    with pytest.raises(ValueError, match="primary_source_present"):
        item(primary_source_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="secondary_source_count"):
        item(secondary_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="consistent_secondary_count"):
        item(consistent_secondary_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="freshness_gap_hours"):
        item(freshness_gap_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="secondary counts"):
        item(
            secondary_source_count=d("1"),
            consistent_secondary_count=d("1"),
            conflicting_secondary_count=d("1"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(item(), paper_only=False)


def test_report_dataclasses_are_frozen_and_manual_reports_validate_digest() -> None:
    consistency_report = report(item())

    with pytest.raises(FrozenInstanceError):
        consistency_report.consistency_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="consistency_status"):
        replace(consistency_report, consistency_status="watch")
    with pytest.raises(ValueError, match="payload_digest"):
        replace(consistency_report, payload_digest="0" * 64)


def test_owned_module_has_no_network_filesystem_or_live_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "source_resolution_primary_secondary_consistency_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite",
        "sqlalchemy",
        "insert ",
        "update ",
        "delete ",
        "live",
        "auth",
        "wallet",
        "private_key",
        "api_key",
        "secret_key",
        "signing",
        "execution",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item_value in value.values():
            values.extend(_walk_payload_values(item_value))
    elif isinstance(value, list):
        for item_value in value:
            values.extend(_walk_payload_values(item_value))
    else:
        values.append(value)
    return tuple(values)
