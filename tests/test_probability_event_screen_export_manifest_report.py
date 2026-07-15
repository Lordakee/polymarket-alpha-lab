from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import json
from pathlib import Path
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_screen_export_manifest_report import (
    PROBABILITY_EVENT_SCREEN_EXPORT_MANIFEST_REPORT_VERSION,
    ProbabilityEventScreenExportManifestInput,
    ProbabilityEventScreenExportManifestReport,
    build_probability_event_screen_export_manifest_report,
    probability_event_screen_export_manifest_report_digest,
    probability_event_screen_export_manifest_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_export_manifest_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def manifest_input(**overrides: object) -> ProbabilityEventScreenExportManifestInput:
    values = {
        "screen_digest_present": True,
        "recommendation_digest_present": True,
        "research_packet_digest_present": True,
        "operator_safety_digest_present": True,
        "supabase_contract_ready": True,
        "redacted_payload_ready": True,
        "ephemeral_log_excluded": True,
        "manual_review_trace_ready": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenExportManifestInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenExportManifestReport:
    return build_probability_event_screen_export_manifest_report(
        manifest_input(**overrides),
    )


def test_all_manifest_artifacts_ready_produces_readonly_payload_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenExportManifestReport
    assert is_dataclass(first)
    assert first.config_version == PROBABILITY_EVENT_SCREEN_EXPORT_MANIFEST_REPORT_VERSION
    assert first.export_manifest_ready is True
    assert first.missing_artifact_count == d("0.000000")
    assert first.ready_ratio == d("1.000000")
    assert first.blocked_reason_codes == ("export_manifest_ready",)
    assert first.attention_reason_codes == ()
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.digest == second.digest
    assert probability_event_screen_export_manifest_report_digest(first) == first.digest

    payload = probability_event_screen_export_manifest_report_payload(first)
    assert payload == first.public_payload
    assert payload["export_manifest_ready"] is True
    assert payload["missing_artifact_count"] == "0.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["digest"] == first.digest
    json.dumps(payload, sort_keys=True)
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["export_manifest_ready"] = False


def test_missing_artifacts_and_attention_roll_up_reason_codes_and_ratio() -> None:
    result = report(
        screen_digest_present=False,
        research_packet_digest_present=False,
        supabase_contract_ready=False,
        redacted_payload_ready=False,
        ephemeral_log_excluded=False,
        manual_review_trace_ready=False,
    )

    assert result.export_manifest_ready is False
    assert result.missing_artifact_count == d("6.000000")
    assert result.ready_ratio == d("0.250000")
    assert result.blocked_reason_codes == (
        "screen_digest_missing",
        "research_packet_digest_missing",
        "supabase_contract_not_ready",
        "redacted_payload_not_ready",
        "manual_review_trace_missing",
    )
    assert result.attention_reason_codes == (
        "ephemeral_log_included_attention",
    )
    assert result.public_payload["missing_artifact_count"] == "6.000000"
    assert result.public_payload["attention_reason_codes"] == (
        "ephemeral_log_included_attention",
    )


def test_ephemeral_log_gap_is_attention_but_not_manifest_blocker() -> None:
    result = report(ephemeral_log_excluded=False)

    assert result.export_manifest_ready is True
    assert result.missing_artifact_count == d("1.000000")
    assert result.ready_ratio == d("0.875000")
    assert result.blocked_reason_codes == ("export_manifest_ready",)
    assert result.attention_reason_codes == (
        "ephemeral_log_included_attention",
    )


def test_dataclasses_are_frozen_flag_guarded_and_decimal_only() -> None:
    input_value = manifest_input()
    result = report()

    with pytest.raises(FrozenInstanceError):
        input_value.screen_digest_present = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.export_manifest_ready = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenExportManifestInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenExportManifestReport):
            pass

    with pytest.raises(ValueError, match="screen_digest_present"):
        manifest_input(screen_digest_present=1)
    with pytest.raises(ValueError, match="paper_only"):
        manifest_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="missing_artifact_count"):
        replace(result, missing_artifact_count=0)  # type: ignore[arg-type]

    numeric_fields = {
        "artifact_count",
        "present_artifact_count",
        "missing_artifact_count",
        "ready_ratio",
    }
    hints = get_type_hints(ProbabilityEventScreenExportManifestReport)
    for field in fields(ProbabilityEventScreenExportManifestReport):
        if field.name in numeric_fields:
            assert hints[field.name] is Decimal
    _assert_public_numeric_values_are_decimal(result)


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)
    assert payload["digest"]

    with pytest.raises(ValueError, match="digest"):
        probability_event_screen_export_manifest_report_payload(
            replace(report(), digest="0" * 64),
        )

    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "postgres://",
        "postgresql://",
        "service_role",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
    ):
        assert forbidden not in encoded

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "web3",
        "private_key",
        "live_trading",
        "place_order",
        "submit_order",
        "cancel_order",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "post",
        "put",
        "rollback",
        "sell",
        "send",
        "sign",
        "upsert",
        "write",
    }
    call_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(name in forbidden_call_names for name in call_names)


def _walk_payload_values(value: object) -> list[object]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(_walk_payload_values(item))
        return values
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_walk_payload_values(item))
        return values
    return [value]


def _is_forbidden_number(value: object) -> bool:
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def _assert_public_numeric_values_are_decimal(
    result: ProbabilityEventScreenExportManifestReport,
) -> None:
    assert type(result.artifact_count) is Decimal
    assert type(result.present_artifact_count) is Decimal
    assert type(result.missing_artifact_count) is Decimal
    assert type(result.ready_ratio) is Decimal
