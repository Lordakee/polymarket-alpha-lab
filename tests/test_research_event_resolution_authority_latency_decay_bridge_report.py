from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_authority_latency_decay_bridge_report.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
RESOLVED_AT = datetime(2026, 7, 6, 10, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_event_resolution_authority_latency_decay_bridge_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(index: int, **overrides: object):
    module = api()
    values = {
        "raw_candidate_id": f"candidate-raw-{index}",
        "market_id": f"market-id-{index}",
        "market_slug": f"will-event-{index}-resolve",
        "market_question": f"Will event {index} resolve?",
        "resolver_reference": f"resolution-authority-{index}",
        "resolver_kind": "official_resolution",
        "event_resolved_at": RESOLVED_AT,
        "authority_observed_at": RESOLVED_AT + timedelta(minutes=5),
        "authority_confidence": d("0.950000"),
        "source_url": f"https://example.invalid/resolution/{index}?token=secret",
        "source_text": f"raw source text {index}",
    }
    values.update(overrides)
    return module.ResearchEventResolutionAuthorityLatencyDecayBridgeObservation(
        **values,
    )


def build_report(*items: object, **overrides: object):
    module = api()
    config = overrides.pop("config", None)
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            observation(1),
            observation(
                2,
                authority_observed_at=RESOLVED_AT + timedelta(minutes=30),
                authority_confidence=d("0.800000"),
            ),
            observation(
                3,
                authority_observed_at=RESOLVED_AT + timedelta(minutes=90),
                authority_confidence=d("0.400000"),
            ),
        )
    return module.build_research_event_resolution_authority_latency_decay_bridge_report(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_or_public_numbers(value: Any) -> None:
    if isinstance(value, float) or type(value) is int or type(value) is Decimal:
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_public_numbers(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_public_numbers(item)


def test_builds_latency_decay_bridge_report_with_pass_watch_block_statuses() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.event_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_latency_seconds == d("2500.000000")
    assert report.average_latency_decay_score == d("0.472222")
    assert report.average_resolver_confidence == d("0.716667")
    assert report.reason_codes == (
        "resolution_authority_latency_report_block_rows",
        "resolution_authority_latency_report_watch_rows",
    )

    rows = report.rows
    assert tuple(row.status for row in rows) == ("block", "watch", "pass")
    assert tuple(row.latency_seconds for row in rows) == (
        d("5400.000000"),
        d("1800.000000"),
        d("300.000000"),
    )
    assert tuple(row.latency_decay_score for row in rows) == (
        d("0.000000"),
        d("0.500000"),
        d("0.916667"),
    )
    assert tuple(row.resolver_confidence for row in rows) == (
        d("0.400000"),
        d("0.800000"),
        d("0.950000"),
    )


def test_row_reason_codes_are_deterministic_and_status_only_pass_watch_block() -> None:
    report = build_report()

    assert api().STATUSES == ("pass", "watch", "block")
    assert report.rows[0].reason_codes == (
        "resolution_authority_bridge_block",
        "resolution_authority_latency_block",
        "resolution_authority_confidence_block",
        "resolution_latency_decay_block",
    )
    assert report.rows[1].reason_codes == (
        "resolution_authority_bridge_watch",
        "resolution_authority_latency_watch",
        "resolution_authority_confidence_watch",
        "resolution_latency_decay_watch",
    )
    assert report.rows[2].reason_codes == (
        "resolution_authority_bridge_pass",
        "resolution_authority_latency_pass",
        "resolution_authority_confidence_pass",
        "resolution_latency_decay_pass",
    )
    assert [item.reason_code for item in report.reason_code_counts] == sorted(
        item.reason_code for item in report.reason_code_counts
    )


def test_public_payload_is_deterministic_digest_backed_and_redacted() -> None:
    module = api()
    report = build_report()
    payload = module.research_event_resolution_authority_latency_decay_bridge_report_to_json_payload(
        report,
    )
    payload_again = (
        module.research_event_resolution_authority_latency_decay_bridge_report_to_json_payload(
            build_report(),
        )
    )

    assert payload == report.payload
    assert payload == payload_again
    assert payload["event_count"] == "3"
    assert payload["average_latency_decay_score"] == "0.472222"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["latency_seconds"] == "5400.000000"
    assert payload["rows"][0]["bridge_digest"] == report.rows[0].bridge_digest
    assert len(payload["rows"][0]["bridge_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert module.validate_research_event_resolution_authority_latency_decay_bridge_report_public_payload(
        payload,
    )
    assert_no_float_or_public_numbers(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    encoded = json.dumps(payload, sort_keys=True)
    forbidden_public_fragments = (
        "candidate-raw-",
        "market-id-",
        "will-event-",
        "Will event",
        "https://example.invalid",
        "raw source text",
        "token=secret",
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "resolver_reference",
    )
    for fragment in forbidden_public_fragments:
        assert fragment not in encoded


def test_empty_report_is_pass_report_only_and_digest_backed() -> None:
    report = build_report(use_default_items=False)

    assert report.status == "pass"
    assert report.event_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.average_latency_seconds == d("0.000000")
    assert report.average_latency_decay_score == d("0.000000")
    assert report.average_resolver_confidence == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("resolution_authority_latency_report_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.ResearchEventResolutionAuthorityLatencyDecayBridgeConfig()
    sample = observation(1)
    report = build_report(sample)
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    decimal_fields = {
        "pass_latency_seconds",
        "block_latency_seconds",
        "decay_window_seconds",
        "pass_resolver_confidence",
        "block_resolver_confidence",
        "pass_latency_decay_score",
        "block_latency_decay_score",
        "authority_confidence",
        "latency_seconds",
        "latency_decay_score",
        "resolver_confidence",
        "event_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_latency_seconds",
        "average_latency_decay_score",
        "average_resolver_confidence",
        "count",
        "event_ratio",
    }

    for item in (config, sample, row, reason_count, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in decimal_fields:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "authority_confidence",
            _DecimalSubclass("0.900000"),
            "authority_confidence must be exactly Decimal",
        ),
        (
            "authority_confidence",
            d("1.000001"),
            "authority_confidence must be <= 1.000000",
        ),
        (
            "authority_confidence",
            d("0.0500004"),
            "authority_confidence must use six decimal places or fewer",
        ),
        (
            "authority_confidence",
            Decimal("NaN"),
            "authority_confidence must be finite",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        observation(1, **{field_name: bad_value})


def test_config_build_and_temporal_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="pass_latency_seconds must be exactly Decimal"):
        module.ResearchEventResolutionAuthorityLatencyDecayBridgeConfig(
            pass_latency_seconds=600,
        )
    with pytest.raises(
        ValueError,
        match="block_latency_seconds must exceed pass_latency_seconds",
    ):
        module.ResearchEventResolutionAuthorityLatencyDecayBridgeConfig(
            block_latency_seconds=d("600.000000"),
        )
    with pytest.raises(
        ValueError,
        match="pass_resolver_confidence must be >= block_resolver_confidence",
    ):
        module.ResearchEventResolutionAuthorityLatencyDecayBridgeConfig(
            pass_resolver_confidence=d("0.400000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchEventResolutionAuthorityLatencyDecayBridgeConfig(
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(1, readonly=False)
    with pytest.raises(ValueError, match="observations must be an iterable"):
        module.build_research_event_resolution_authority_latency_decay_bridge_report(
            object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations must contain"):
        module.build_research_event_resolution_authority_latency_decay_bridge_report(
            [object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_authority_latency_decay_bridge_report(
            [observation(1)],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="authority_observed_at must not precede"):
        observation(1, authority_observed_at=RESOLVED_AT - timedelta(seconds=1))
    with pytest.raises(ValueError, match="must not be after generated_at"):
        build_report(
            observation(1, authority_observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    duplicate = observation(1)
    with pytest.raises(ValueError, match="duplicate bridge keys"):
        build_report(duplicate, duplicate)


def test_digest_and_public_payload_validation_reject_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="event counts must match rows"):
        replace(report, pass_count=d("2"), derived_validation_digest="")
    with pytest.raises(ValueError, match="reason_codes must match status"):
        replace(
            report,
            reason_codes=("resolution_authority_latency_report_empty",),
            derived_validation_digest="",
        )

    payload = dict(report.payload)
    payload["event_count"] = "4"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_resolution_authority_latency_decay_bridge_report_public_payload(
            payload,
        )

    payload = dict(report.payload)
    payload["wallet"] = "redacted"
    payload["derived_validation_digest"] = module._public_payload_derived_validation_digest(
        payload,
    )
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_event_resolution_authority_latency_decay_bridge_report_public_payload(
            payload,
        )


def test_module_scope_has_no_database_network_wallet_order_or_trade_surface() -> None:
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
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sql",
        "subprocess",
        "urllib",
        "wallet",
        "web3",
    )
    allowed_imports = {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    assert set(imports) <= allowed_imports
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    forbidden_call_or_attribute_fragments = (
        "connect",
        "dsn",
        "execute",
        "fetch",
        "network",
        "order",
        "post",
        "request",
        "send",
        "sign",
        "sizing",
        "table",
        "trade",
        "wallet",
    )
    assert not any(
        fragment in name.lower()
        for name in call_names + attribute_names
        for fragment in forbidden_call_or_attribute_fragments
    )
    assert float_constants == []
