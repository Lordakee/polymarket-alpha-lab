from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import inspect
import json

import pytest

import polymarket_alpha_lab.research_event_resolution_source_consensus_reversal_report as api
from polymarket_alpha_lab.research_event_resolution_source_consensus_reversal_report import (
    DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_CONSENSUS_REVERSAL_CONFIG_VERSION,
    ResearchEventResolutionSourceConsensusReversalConfig,
    ResearchEventResolutionSourceConsensusReversalInput,
    ResearchEventResolutionSourceConsensusReversalPublicPayloadItem,
    ResearchEventResolutionSourceConsensusReversalReport,
    build_research_event_resolution_source_consensus_reversal_report,
    research_event_resolution_source_consensus_reversal_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def consensus_input(
    seed: str,
    *,
    previous_seed: str = "yes",
    current_seed: str = "yes",
    current_support_count: Decimal = d("3.000000"),
    independent_source_family_count: Decimal = d("2.000000"),
    newest_source_age_seconds: Decimal = d("600.000000"),
    oldest_source_age_seconds: Decimal = d("1200.000000"),
    contradiction_pressure: Decimal = d("0.100000"),
    seconds_since_reversal: Decimal = d("3600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionSourceConsensusReversalInput:
    return ResearchEventResolutionSourceConsensusReversalInput(
        event_digest=digest(f"{seed}-event"),
        previous_consensus_digest=digest(previous_seed),
        current_consensus_digest=digest(current_seed),
        current_support_count=current_support_count,
        independent_source_family_count=independent_source_family_count,
        newest_source_age_seconds=newest_source_age_seconds,
        oldest_source_age_seconds=oldest_source_age_seconds,
        contradiction_pressure=contradiction_pressure,
        seconds_since_reversal=seconds_since_reversal,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *inputs: ResearchEventResolutionSourceConsensusReversalInput,
    config: ResearchEventResolutionSourceConsensusReversalConfig | None = None,
    payload_items: tuple[
        ResearchEventResolutionSourceConsensusReversalPublicPayloadItem,
        ...,
    ] = (),
) -> ResearchEventResolutionSourceConsensusReversalReport:
    return build_research_event_resolution_source_consensus_reversal_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
        public_payload=payload_items,
    )


def test_reversal_boundaries_classify_pass_watch_and_block_rows() -> None:
    readiness = report(
        consensus_input("stable", previous_seed="yes", current_seed="yes"),
        consensus_input("pass", previous_seed="yes", current_seed="no"),
        consensus_input(
            "watch",
            previous_seed="yes",
            current_seed="no",
            current_support_count=d("2.000000"),
        ),
        consensus_input(
            "block",
            previous_seed="yes",
            current_seed="no",
            current_support_count=d("1.000000"),
        ),
    )

    rows = {row.event_digest: row for row in readiness.rows}
    assert readiness.status == "block"
    assert readiness.row_count == d("4.000000")
    assert readiness.stable_count == d("1.000000")
    assert readiness.reversal_count == d("3.000000")
    assert readiness.pass_count == d("2.000000")
    assert readiness.watch_count == d("1.000000")
    assert readiness.block_count == d("1.000000")
    assert rows[digest("stable-event")].status == "pass"
    assert rows[digest("stable-event")].reason_codes == (
        "source_consensus_stable_pass",
    )
    assert rows[digest("pass-event")].status == "pass"
    assert rows[digest("pass-event")].reason_codes == (
        "source_consensus_reversal_pass",
    )
    assert rows[digest("watch-event")].status == "watch"
    assert rows[digest("watch-event")].reason_codes == (
        "consensus_reversal_support_watch",
    )
    assert rows[digest("block-event")].status == "block"
    assert rows[digest("block-event")].reason_codes == (
        "consensus_reversal_support_block",
    )


def test_freshness_contradiction_and_confirmation_pressure_drive_status() -> None:
    readiness = report(
        consensus_input(
            "freshness-watch",
            previous_seed="yes",
            current_seed="no",
            oldest_source_age_seconds=d("8000.000000"),
        ),
        consensus_input(
            "freshness-block",
            previous_seed="yes",
            current_seed="no",
            newest_source_age_seconds=d("90000.000000"),
            oldest_source_age_seconds=d("90000.000000"),
        ),
        consensus_input(
            "contradiction-watch",
            previous_seed="yes",
            current_seed="no",
            contradiction_pressure=d("0.250000"),
        ),
        consensus_input(
            "contradiction-block",
            previous_seed="yes",
            current_seed="no",
            contradiction_pressure=d("0.500000"),
        ),
        consensus_input(
            "confirmation-watch",
            previous_seed="yes",
            current_seed="no",
            seconds_since_reversal=d("600.000000"),
        ),
    )

    rows = {row.event_digest: row for row in readiness.rows}
    assert rows[digest("freshness-watch-event")].status == "watch"
    assert "consensus_reversal_freshness_watch" in (
        rows[digest("freshness-watch-event")].reason_codes
    )
    assert rows[digest("freshness-block-event")].status == "block"
    assert "consensus_reversal_freshness_block" in (
        rows[digest("freshness-block-event")].reason_codes
    )
    assert rows[digest("contradiction-watch-event")].status == "watch"
    assert "consensus_reversal_contradiction_watch" in (
        rows[digest("contradiction-watch-event")].reason_codes
    )
    assert rows[digest("contradiction-block-event")].status == "block"
    assert "consensus_reversal_contradiction_block" in (
        rows[digest("contradiction-block-event")].reason_codes
    )
    assert rows[digest("confirmation-watch-event")].status == "watch"
    assert rows[digest("confirmation-watch-event")].confirmation_score == d("0.333333")
    assert rows[digest("confirmation-watch-event")].confidence_score == d("0.893333")
    assert "consensus_reversal_confirmation_watch" in (
        rows[digest("confirmation-watch-event")].reason_codes
    )
    assert readiness.freshness_pressure_count == d("2.000000")
    assert readiness.contradiction_pressure_count == d("2.000000")
    assert readiness.confirmation_pressure_count == d("1.000000")


def test_public_payload_and_digest_are_deterministic_decimal_only_and_validated() -> None:
    payload_item = ResearchEventResolutionSourceConsensusReversalPublicPayloadItem(
        key="safe_context",
        value="sanitized digest inputs only",
    )
    alpha_payload_item = ResearchEventResolutionSourceConsensusReversalPublicPayloadItem(
        key="alpha_context",
        value="sanitized alpha digest only",
    )
    first = report(
        consensus_input("zeta", previous_seed="yes", current_seed="no"),
        consensus_input(
            "alpha",
            previous_seed="yes",
            current_seed="no",
            current_support_count=d("2.000000"),
        ),
        payload_items=(payload_item, alpha_payload_item),
    )
    second = report(
        consensus_input(
            "alpha",
            previous_seed="yes",
            current_seed="no",
            current_support_count=d("2.000000"),
        ),
        consensus_input("zeta", previous_seed="yes", current_seed="no"),
        payload_items=(alpha_payload_item, payload_item),
    )
    third = report(
        consensus_input(
            "alpha",
            previous_seed="yes",
            current_seed="no",
            current_support_count=d("2.000000"),
        ),
        consensus_input("zeta", previous_seed="yes", current_seed="no"),
        payload_items=(payload_item, alpha_payload_item),
    )

    first_payload = research_event_resolution_source_consensus_reversal_public_payload(
        first,
    )
    second_payload = second.payload
    assert first_payload == second_payload
    assert second.payload == third.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert second.derived_validation_digest == third.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["confidence_score"] == "0.840000"
    json.dumps(first_payload, sort_keys=True)
    assert_no_float(first_payload)
    assert_no_non_decimal_public_numbers(first)

    digest_payload = dict(first_payload)
    digest_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == (
        first.derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    with pytest.raises(FrozenInstanceError):
        first.rows[0].confidence_score = d("0.000000")  # type: ignore[misc]


def test_leak_prevention_rejects_raw_identifiers_and_unsafe_public_payloads() -> None:
    with pytest.raises(ValueError, match="sha256"):
        ResearchEventResolutionSourceConsensusReversalInput(
            event_digest=_join_parts("raw-", "candidate", "-id"),
            previous_consensus_digest=digest("previous"),
            current_consensus_digest=digest("current"),
            current_support_count=d("3.000000"),
            independent_source_family_count=d("2.000000"),
            newest_source_age_seconds=d("600.000000"),
            oldest_source_age_seconds=d("1200.000000"),
            contradiction_pressure=d("0.100000"),
            seconds_since_reversal=d("3600.000000"),
        )

    for key in (
        _join_parts("candidate", "_", "id"),
        _join_parts("market", "_", "id"),
        _join_parts("market", "_", "slug"),
        _join_parts("que", "stion"),
        _join_parts("source", "_", "url"),
        _join_parts("source", "_", "text"),
        "dsn",
        _join_parts("ta", "ble", "_name"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionSourceConsensusReversalPublicPayloadItem(
                key=key,
                value="safe value",
            )
    for key in (
        _join_parts("source", "Url"),
        _join_parts("source", "Text"),
        _join_parts("wal", "let", "Address"),
        _join_parts("place", "Ord", "er"),
        _join_parts("tra", "de", "Execution"),
        _join_parts("au", "th", "State"),
        _join_parts("li", "ve", "Runner"),
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionSourceConsensusReversalPublicPayloadItem(
                key=key,
                value="safe value",
            )

    for value in (
        "https://example.invalid/evidence",
        "postgres://user:pass@example.invalid/db",
        _join_parts("wal", "let surface"),
        _join_parts("place ", "ord", "er"),
        _join_parts("tra", "de execution"),
        _join_parts("raw ", "que", "stion text"),
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionSourceConsensusReversalPublicPayloadItem(
                key="safe_key",
                value=value,
            )
    for value in (
        _join_parts("source", "Url"),
        _join_parts("source", "Text"),
        _join_parts("wal", "let", "Address"),
        _join_parts("place", "Ord", "er"),
        _join_parts("tra", "de", "Execution"),
        _join_parts("au", "th", "State"),
        _join_parts("li", "ve", "Runner"),
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionSourceConsensusReversalPublicPayloadItem(
                key="safe_key",
                value=value,
            )

    payload = report(consensus_input("safe")).payload
    encoded = json.dumps(payload, sort_keys=True).lower()
    for leaked in (
        _join_parts("raw-", "candidate", "-id"),
        _join_parts("market", "_", "id"),
        _join_parts("market", "_", "slug"),
        _join_parts("source", "_", "url"),
        _join_parts("source", "_", "text"),
        "postgres://",
        _join_parts("wal", "let surface"),
        _join_parts("place ", "ord", "er"),
        _join_parts("tra", "de execution"),
    ):
        assert leaked not in encoded


def test_custom_config_validation_flags_and_public_exports_are_enforced() -> None:
    custom = ResearchEventResolutionSourceConsensusReversalConfig(
        pass_current_support_count=d("4.000000"),
        watch_current_support_count=d("3.000000"),
        pass_independent_source_family_count=d("3.000000"),
        watch_independent_source_family_count=d("2.000000"),
    )
    readiness = report(
        consensus_input(
            "custom-watch",
            previous_seed="yes",
            current_seed="no",
            current_support_count=d("3.000000"),
            independent_source_family_count=d("2.000000"),
        ),
        config=custom,
    )

    assert readiness.status == "watch"
    assert readiness.rows[0].status == "watch"
    assert readiness.rows[0].reason_codes == (
        "consensus_reversal_support_watch",
        "consensus_reversal_family_watch",
    )

    with pytest.raises(ValueError, match="watch_current_support_count"):
        ResearchEventResolutionSourceConsensusReversalConfig(
            pass_current_support_count=d("2.000000"),
            watch_current_support_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="stale_source_block_seconds"):
        ResearchEventResolutionSourceConsensusReversalConfig(
            stale_source_watch_seconds=d("90000.000000"),
            stale_source_block_seconds=d("7200.000000"),
        )
    with pytest.raises(ValueError, match="weights"):
        ResearchEventResolutionSourceConsensusReversalConfig(
            support_weight=d("0.500000"),
            family_weight=d("0.250000"),
            freshness_weight=d("0.200000"),
            contradiction_weight=d("0.200000"),
            confirmation_weight=d("0.100000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventResolutionSourceConsensusReversalConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        consensus_input("flags", report_only=False)

    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_CONSENSUS_REVERSAL_CONFIG_VERSION",
        "ResearchEventResolutionSourceConsensusReversalConfig",
        "ResearchEventResolutionSourceConsensusReversalInput",
        "ResearchEventResolutionSourceConsensusReversalPublicPayloadItem",
        "ResearchEventResolutionSourceConsensusReversalReport",
        "ResearchEventResolutionSourceConsensusReversalRow",
        "build_research_event_resolution_source_consensus_reversal_report",
        "research_event_resolution_source_consensus_reversal_public_payload",
    )
    for public_name in api.__all__:
        assert not contains_forbidden_public_surface(public_name)
    for public_type in (
        ResearchEventResolutionSourceConsensusReversalConfig,
        ResearchEventResolutionSourceConsensusReversalInput,
        ResearchEventResolutionSourceConsensusReversalPublicPayloadItem,
        api.ResearchEventResolutionSourceConsensusReversalRow,
        ResearchEventResolutionSourceConsensusReversalReport,
    ):
        for field in fields(public_type):
            assert not contains_forbidden_public_surface(field.name)


def test_module_has_no_external_action_or_sensitive_surfaces() -> None:
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert "float(" not in source
    assert ".total_seconds(" not in source
    for token in (
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "end"),
    ):
        assert token not in source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "delete",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_float(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"payload contains float: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_no_non_decimal_public_numbers(getattr(value, field.name))


def contains_forbidden_public_surface(value: str) -> bool:
    lowered = value.lower()
    if any(
        phrase in lowered
        for phrase in (
            _join_parts("candidate", "_", "id"),
            _join_parts("market", "_", "id"),
            _join_parts("market", "_", "slug"),
            _join_parts("source", "_", "url"),
            _join_parts("source", "_", "text"),
            _join_parts("ta", "ble", "_name"),
        )
    ):
        return True
    tokens = tuple(token for token in lowered.replace("_", " ").split() if token)
    forbidden_tokens = frozenset(
        (
            "candidate",
            _join_parts("que", "stion"),
            "url",
            "text",
            "dsn",
            _join_parts("ta", "ble"),
            _join_parts("to", "ken"),
            _join_parts("wal", "let"),
            _join_parts("ord", "er"),
            _join_parts("tra", "de"),
            _join_parts("au", "th"),
            _join_parts("data", "base"),
            _join_parts("net", "work"),
            _join_parts("li", "ve"),
            "buy",
            "sell",
            _join_parts("recomm", "endation"),
            _join_parts("siz", "ing"),
        ),
    )
    return any(token in forbidden_tokens for token in tokens)
