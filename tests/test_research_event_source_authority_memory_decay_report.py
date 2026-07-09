from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import json
from pathlib import Path

import pytest


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_source_authority_memory_decay_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def _api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_source_authority_memory_decay_report",
    )


def _config(api):
    return api.EventSourceAuthorityMemoryDecayConfig(
        authority_memory_watch_seconds=Decimal("500.000000"),
        authority_memory_block_seconds=Decimal("1000.000000"),
        memory_decay_weight=Decimal("0.500000"),
        min_pass_effective_authority_score=Decimal("0.700000"),
        min_watch_effective_authority_score=Decimal("0.450000"),
        min_parse_confidence=Decimal("0.600000"),
        contradiction_block_ratio=Decimal("0.500000"),
    )


def _observation(
    api,
    *,
    event_ref_digest: str = "a" * 64,
    authority_ref_digest: str = "1" * 64,
    observed_delta: timedelta = timedelta(seconds=250),
    authority_score: Decimal = Decimal("0.900000"),
    parse_confidence: Decimal = Decimal("0.900000"),
    confirmation_count: Decimal = Decimal("3.000000"),
    contradiction_count: Decimal = Decimal("0.000000"),
):
    return api.EventAuthorityObservation(
        event_ref_digest=event_ref_digest,
        authority_ref_digest=authority_ref_digest,
        observed_at=NOW - observed_delta,
        authority_score=authority_score,
        parse_confidence=parse_confidence,
        confirmation_count=confirmation_count,
        contradiction_count=contradiction_count,
    )


def _report(api, observations, *, config=None):
    return api.build_research_event_source_authority_memory_decay_report(
        observations,
        generated_at=NOW,
        config=config if config is not None else _config(api),
    )


def test_scores_authority_memory_decay_and_status_counts_deterministically() -> None:
    api = _api()
    config = _config(api)

    report = _report(
        api,
        (
            _observation(api, event_ref_digest="b" * 64),
            _observation(
                api,
                event_ref_digest="a" * 64,
                observed_delta=timedelta(seconds=600),
                authority_score=Decimal("0.800000"),
            ),
            _observation(
                api,
                event_ref_digest="c" * 64,
                observed_delta=timedelta(seconds=1000),
            ),
        ),
        config=config,
    )

    assert report.status == "block"
    assert report.observation_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.stale_memory_count == Decimal("2.000000")
    assert report.low_authority_count == Decimal("2.000000")
    assert report.parse_uncertainty_count == Decimal("0.000000")
    assert report.max_memory_age_seconds == Decimal("1000.000000")
    assert report.average_effective_authority_score == Decimal("0.599167")

    watch_row, pass_row, block_row = report.rows
    assert watch_row.event_ref_digest == "a" * 64
    assert watch_row.memory_age_seconds == Decimal("600.000000")
    assert watch_row.memory_decay_ratio == Decimal("0.600000")
    assert watch_row.effective_authority_score == Decimal("0.560000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == ("memory_watch", "authority_below_pass")

    assert pass_row.event_ref_digest == "b" * 64
    assert pass_row.memory_decay_ratio == Decimal("0.250000")
    assert pass_row.effective_authority_score == Decimal("0.787500")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("authority_memory_pass",)

    assert block_row.event_ref_digest == "c" * 64
    assert block_row.memory_decay_ratio == Decimal("1.000000")
    assert block_row.effective_authority_score == Decimal("0.450000")
    assert block_row.status == "block"
    assert block_row.reason_codes == ("memory_block", "authority_below_pass")


def test_public_payload_is_deterministic_decimal_serialized_and_digest_validated() -> None:
    api = _api()
    config = _config(api)
    observations = (
        _observation(api, event_ref_digest="b" * 64),
        _observation(
            api,
            event_ref_digest="a" * 64,
            observed_delta=timedelta(seconds=600),
            authority_score=Decimal("0.800000"),
        ),
    )

    first = _report(api, observations, config=config)
    second = _report(api, tuple(reversed(observations)), config=config)

    assert first.payload == second.payload
    payload = first.payload
    payload_without_digest = dict(payload)
    digest = payload_without_digest.pop("derived_validation_digest")
    encoded = json.dumps(payload_without_digest, sort_keys=True, separators=(",", ":"))
    assert api.sha256_public_payload_digest(payload_without_digest) == digest
    assert api.validate_research_event_source_authority_memory_decay_public_payload(payload)
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["memory_age_seconds"] == "600.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert json.loads(encoded)["rows"][0]["effective_authority_score"] == "0.560000"
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(first)

    tampered = json.loads(json.dumps(payload))
    tampered["rows"][0]["effective_authority_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_research_event_source_authority_memory_decay_public_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, generated_at=NOW + timedelta(seconds=1))


def test_dataclasses_are_frozen_exact_decimal_only_report_only_types() -> None:
    api = _api()
    observation = _observation(api)
    report = _report(api, (observation,))

    with pytest.raises(FrozenInstanceError):
        observation.authority_score = Decimal("0.100000")  # type: ignore[misc]

    for cls in (
        api.EventSourceAuthorityMemoryDecayConfig,
        api.EventAuthorityObservation,
        api.ResearchEventSourceAuthorityMemoryDecayRow,
        api.ResearchEventSourceAuthorityMemoryDecayReport,
    ):
        with pytest.raises(TypeError):

            class Bad(cls):  # type: ignore[misc, valid-type]
                pass

    for value in (api.EventSourceAuthorityMemoryDecayConfig(), observation, report.rows[0], report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        _observation(api, authority_score=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        _observation(api, authority_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    for dataclass_value in (
        api.EventSourceAuthorityMemoryDecayConfig(),
        observation,
        report.rows[0],
        report,
    ):
        _assert_no_non_decimal_public_numbers(dataclass_value)


def test_public_payload_excludes_sensitive_inputs_and_runtime_capabilities() -> None:
    api = _api()
    report = _report(api, (_observation(api),))

    _assert_public_payload_is_safe(report.payload)
    for cls in (
        api.EventSourceAuthorityMemoryDecayConfig,
        api.EventAuthorityObservation,
        api.ResearchEventSourceAuthorityMemoryDecayRow,
        api.ResearchEventSourceAuthorityMemoryDecayReport,
    ):
        for field in fields(cls):
            _assert_safe_fragment(field.name)

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

    for unsafe_key in (
        "candidate_ref",
        "market_ref",
        "source_ref",
        "raw_url",
        "raw_text",
        "dsn_ref",
        "table_ref",
        "token_ref",
        "wallet_ref",
        "order_ref",
        "live_trading",
        "network_ref",
        "database_ref",
        "sizing_ref",
        "recommendation_ref",
        "auth_token_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            api._reject_unsafe_public_payload(
                "example",
                {unsafe_key: "redacted"},
                allow_json_containers=True,
            )


def test_valid_digest_values_are_not_treated_as_raw_database_leakage() -> None:
    api = _api()
    report = _report(
        api,
        (
            _observation(
                api,
                event_ref_digest="db" * 32,
                authority_ref_digest="cd" * 32,
            ),
        ),
    )

    assert report.payload["rows"][0]["event_ref_digest"] == "db" * 32
    assert api.validate_research_event_source_authority_memory_decay_public_payload(
        report.payload,
    )


def test_module_has_no_float_database_network_or_execution_surfaces() -> None:
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
        "rollback",
        "send",
        "total_seconds",
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
        assert type(value) is Decimal
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


def _assert_public_payload_is_safe(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_safe_fragment(key)
            _assert_public_payload_is_safe(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_public_payload_is_safe(item)
        return
    if isinstance(value, str):
        _assert_safe_fragment(value)


def _assert_safe_fragment(value: str) -> None:
    lowered = value.lower()
    forbidden_fragments = (
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "live",
        "trading",
        "network",
        "database",
        "sizing",
        "recommendation",
        "auth_token",
        "oauth",
        "://",
        "http",
    )
    assert not any(fragment in lowered for fragment in forbidden_fragments), value
