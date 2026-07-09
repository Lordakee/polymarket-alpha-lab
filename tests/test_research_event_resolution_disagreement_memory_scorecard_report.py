import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_disagreement_memory_scorecard_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_event_resolution_disagreement_memory_scorecard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def event(
    event_id: str,
    *,
    observed_hours_ago: int = 2,
    resolved_hours_ago: int = 24,
    current_resolution_disagreement_score: Decimal = d("0.200000"),
    previous_resolution_disagreement_score: Decimal = d("0.600000"),
    disagreement_memory_decay_score: Decimal = d("0.100000"),
    resolution_confirmation_score: Decimal = d("0.800000"),
    evidence_family_count: Decimal = d("3"),
    conflicting_family_count: Decimal = d("1"),
    raw_candidate_text: str = "candidate text from https://example.invalid/private?token=secret",
    source_url: str = "postgres://user:token@example.invalid/table",
):
    module = api()
    return module.EventResolutionDisagreementMemoryInput(
        event_id=event_id,
        event_type="macro_resolution",
        observed_at=GENERATED_AT - timedelta(hours=observed_hours_ago),
        resolved_at=GENERATED_AT - timedelta(hours=resolved_hours_ago),
        current_resolution_disagreement_score=current_resolution_disagreement_score,
        previous_resolution_disagreement_score=previous_resolution_disagreement_score,
        disagreement_memory_decay_score=disagreement_memory_decay_score,
        resolution_confirmation_score=resolution_confirmation_score,
        evidence_family_count=evidence_family_count,
        conflicting_family_count=conflicting_family_count,
        raw_candidate_text=raw_candidate_text,
        source_url=source_url,
    )


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "watch_disagreement_score": d("0.300000"),
        "block_disagreement_score": d("0.700000"),
        "watch_memory_score": d("0.300000"),
        "block_memory_score": d("0.700000"),
        "min_resolution_confirmation_score": d("0.500000"),
    }
    values.update(overrides)
    return module.EventResolutionDisagreementMemoryScorecardConfig(**values)


def build_report(*events: object):
    module = api()
    return module.build_research_event_resolution_disagreement_memory_scorecard_report(
        events,
        config=config(),
        generated_at=GENERATED_AT,
    )


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_raw_or_sensitive_fragments(value: object) -> None:
    forbidden = (
        "candidate",
        "market",
        "source_url",
        "raw_candidate_text",
        "https://",
        "postgres://",
        "token",
        "secret",
        "dsn",
        "table",
    )
    if type(value) is str:
        lowered = value.lower()
        for fragment in forbidden:
            assert fragment not in lowered
        return
    if type(value) is dict:
        for key, item in value.items():
            assert_no_raw_or_sensitive_fragments(key)
            assert_no_raw_or_sensitive_fragments(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_no_raw_or_sensitive_fragments(item)


def assert_no_float_or_int_values(value: object) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_or_int_values(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_or_int_values(item)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def public_reference(raw_value: str) -> str:
    return sha256(raw_value.encode()).hexdigest()


def test_builds_deterministic_pass_watch_block_scorecard_without_raw_leakage() -> None:
    module = api()
    first = build_report(
        event(
            "evt-watch",
            current_resolution_disagreement_score=d("0.400000"),
            previous_resolution_disagreement_score=d("0.450000"),
            disagreement_memory_decay_score=d("0.250000"),
        ),
        event(
            "evt-block",
            current_resolution_disagreement_score=d("0.800000"),
            previous_resolution_disagreement_score=d("0.900000"),
            disagreement_memory_decay_score=d("0.850000"),
            resolution_confirmation_score=d("0.200000"),
        ),
        event(
            "evt-pass",
            current_resolution_disagreement_score=d("0.050000"),
            previous_resolution_disagreement_score=d("0.100000"),
            disagreement_memory_decay_score=d("0.050000"),
        ),
    )
    second = build_report(
        event(
            "evt-pass",
            current_resolution_disagreement_score=d("0.050000"),
            previous_resolution_disagreement_score=d("0.100000"),
            disagreement_memory_decay_score=d("0.050000"),
        ),
        event(
            "evt-block",
            current_resolution_disagreement_score=d("0.800000"),
            previous_resolution_disagreement_score=d("0.900000"),
            disagreement_memory_decay_score=d("0.850000"),
            resolution_confirmation_score=d("0.200000"),
        ),
        event(
            "evt-watch",
            current_resolution_disagreement_score=d("0.400000"),
            previous_resolution_disagreement_score=d("0.450000"),
            disagreement_memory_decay_score=d("0.250000"),
        ),
    )

    assert first.rows == second.rows
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.status == "block"
    assert first.event_count == d("3.000000")
    assert first.pass_count == d("1.000000")
    assert first.watch_count == d("1.000000")
    assert first.block_count == d("1.000000")
    assert first.rows[0].event_reference == public_reference("evt-block")
    assert first.rows[0].status == "block"
    assert first.rows[1].event_reference == public_reference("evt-watch")
    assert first.rows[1].status == "watch"
    assert first.rows[2].event_reference == public_reference("evt-pass")
    assert first.rows[2].status == "pass"

    payload = module.research_event_resolution_disagreement_memory_scorecard_report_payload(
        first,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["event_count"] == "3.000000"
    assert payload["rows"][0]["event_reference"] == public_reference("evt-block")
    assert "event_id" not in payload["rows"][0]
    assert payload["rows"][0]["status"] == "block"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    encoded_payload = json.dumps(payload, sort_keys=True)
    assert "evt-block" not in encoded_payload
    assert "evt-watch" not in encoded_payload
    assert "evt-pass" not in encoded_payload
    assert_no_float_or_int_values(payload)
    assert_no_raw_or_sensitive_fragments(payload)
    module.validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
        payload,
    )


def test_payload_digest_rejects_tampering_and_downgraded_flags() -> None:
    module = api()
    report = build_report(event("evt-watch"))
    payload = module.research_event_resolution_disagreement_memory_scorecard_report_payload(
        report,
    )

    tampered = dict(payload)
    tampered["watch_count"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
            tampered,
        )

    downgraded = dict(payload)
    downgraded["readonly"] = False
    downgraded["derived_validation_digest"] = canonical_digest(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
            downgraded,
        )

    unsafe = dict(payload)
    unsafe["source_url"] = "https://example.invalid/private?token=secret"
    unsafe["derived_validation_digest"] = canonical_digest(unsafe)
    with pytest.raises(ValueError, match="unsafe|raw|sensitive"):
        module.validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
            unsafe,
        )


def test_public_payload_requires_complete_canonical_schema() -> None:
    module = api()
    report = build_report(event("evt-watch"))
    payload = module.research_event_resolution_disagreement_memory_scorecard_report_payload(
        report,
    )

    missing_top_level = dict(payload)
    missing_top_level.pop("generated_at")
    missing_top_level["derived_validation_digest"] = canonical_digest(missing_top_level)
    with pytest.raises(ValueError, match="missing public field.*generated_at"):
        module.validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
            missing_top_level,
        )

    malformed_datetime = dict(payload)
    malformed_datetime["generated_at"] = "not-a-datetime"
    malformed_datetime["derived_validation_digest"] = canonical_digest(malformed_datetime)
    with pytest.raises(ValueError, match="generated_at.*datetime"):
        module.validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
            malformed_datetime,
        )

    missing_row_field = dict(payload)
    row_without_observed_at = dict(payload["rows"][0])
    row_without_observed_at.pop("observed_at")
    missing_row_field["rows"] = [row_without_observed_at]
    missing_row_field["derived_validation_digest"] = canonical_digest(missing_row_field)
    with pytest.raises(ValueError, match="missing public field.*observed_at"):
        module.validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
            missing_row_field,
        )

    unsafe_row_reference = dict(payload)
    row_with_unsafe_reference = dict(payload["rows"][0])
    row_with_unsafe_reference["event_reference"] = "wallet-order-trade"
    unsafe_row_reference["rows"] = [row_with_unsafe_reference]
    unsafe_row_reference["derived_validation_digest"] = canonical_digest(
        unsafe_row_reference,
    )
    with pytest.raises(ValueError, match="unsafe|raw|sensitive"):
        module.validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
            unsafe_row_reference,
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    item = event("evt-watch")
    report = build_report(item)

    for value in (config(), item, report.rows[0], report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        event("evt-int", current_resolution_disagreement_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        event("evt-float", current_resolution_disagreement_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        event(
            "evt-subclass",
            current_resolution_disagreement_score=_DecimalSubclass("0.500000"),
        )


def test_rejects_invalid_status_and_unsafe_public_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="status"):
        module.EventResolutionDisagreementMemoryScorecardRow(
            event_reference=public_reference("evt-invalid"),
            event_type="macro_resolution",
            observed_at=GENERATED_AT - timedelta(hours=1),
            resolved_at=GENERATED_AT - timedelta(hours=2),
            current_resolution_disagreement_score=d("0.100000"),
            previous_resolution_disagreement_score=d("0.100000"),
            disagreement_memory_decay_score=d("0.100000"),
            resolution_confirmation_score=d("0.900000"),
            evidence_family_count=d("2.000000"),
            conflicting_family_count=d("0.000000"),
            memory_score=d("0.100000"),
            disagreement_delta=d("0.000000"),
            status="ready",
            reason_codes=("event_resolution_disagreement_memory_pass",),
        )

    with pytest.raises(ValueError, match="future|after"):
        module.build_research_event_resolution_disagreement_memory_scorecard_report(
            (event("evt-future", observed_hours_ago=-1),),
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_module_scope_has_no_database_network_wallet_order_or_trading_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "order",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "post",
        "recommend",
        "rollback",
        "send",
        "size",
        "trade",
        "wallet",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
