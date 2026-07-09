from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import inspect
import json

import pytest

import polymarket_alpha_lab.research_event_resolution_claim_freshness_decay_ladder_report as api
from polymarket_alpha_lab.research_event_resolution_claim_freshness_decay_ladder_report import (
    RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_STATUSES,
    ResearchEventResolutionClaimFreshnessDecayLadderConfig,
    ResearchEventResolutionClaimFreshnessDecayLadderInput,
    ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem,
    ResearchEventResolutionClaimFreshnessDecayLadderReport,
    ResearchEventResolutionClaimFreshnessDecayLadderRow,
    build_research_event_resolution_claim_freshness_decay_ladder_report,
    research_event_resolution_claim_freshness_decay_ladder_public_payload,
    research_event_resolution_claim_freshness_decay_ladder_report_digest,
    validate_research_event_resolution_claim_freshness_decay_ladder_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def claim_input(
    seed: str = "claim-a",
    *,
    claim_age_seconds: Decimal = d("600.000000"),
    confirmation_age_seconds: Decimal = d("600.000000"),
    corroborating_claim_count: Decimal = d("3.000000"),
    independent_signal_count: Decimal = d("2.000000"),
    contradiction_pressure: Decimal = d("0.100000"),
    resolution_update_latency_seconds: Decimal = d("600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionClaimFreshnessDecayLadderInput:
    return ResearchEventResolutionClaimFreshnessDecayLadderInput(
        claim_digest=digest(f"{seed}-claim"),
        resolution_digest=digest(f"{seed}-resolution"),
        evidence_digest=digest(f"{seed}-evidence"),
        claim_age_seconds=claim_age_seconds,
        confirmation_age_seconds=confirmation_age_seconds,
        corroborating_claim_count=corroborating_claim_count,
        independent_signal_count=independent_signal_count,
        contradiction_pressure=contradiction_pressure,
        resolution_update_latency_seconds=resolution_update_latency_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *inputs: ResearchEventResolutionClaimFreshnessDecayLadderInput,
    config: ResearchEventResolutionClaimFreshnessDecayLadderConfig | None = None,
    payload_items: tuple[ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem, ...] = (),
) -> ResearchEventResolutionClaimFreshnessDecayLadderReport:
    return build_research_event_resolution_claim_freshness_decay_ladder_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
        public_payload=payload_items,
    )


def test_freshness_ladder_classifies_pass_watch_and_block_rows() -> None:
    readiness = report(
        claim_input("pass"),
        claim_input("watch", claim_age_seconds=d("21600.000000")),
        claim_input(
            "block",
            claim_age_seconds=d("86401.000000"),
            confirmation_age_seconds=d("172801.000000"),
            corroborating_claim_count=ZERO,
            independent_signal_count=ZERO,
        ),
    )

    rows = {row.claim_digest: row for row in readiness.rows}
    assert readiness.status == "block"
    assert readiness.row_count == d("3.000000")
    assert readiness.pass_count == d("1.000000")
    assert readiness.watch_count == d("1.000000")
    assert readiness.block_count == d("1.000000")
    assert rows[digest("pass-claim")].status == "pass"
    assert rows[digest("pass-claim")].reason_codes == (
        "claim_freshness_decay_ladder_pass",
    )
    assert rows[digest("watch-claim")].status == "watch"
    assert rows[digest("watch-claim")].reason_codes == (
        "claim_freshness_watch",
    )
    assert rows[digest("block-claim")].status == "block"
    assert rows[digest("block-claim")].reason_codes == (
        "claim_freshness_block",
        "confirmation_freshness_block",
        "corroborating_claim_quorum_block",
        "independent_signal_quorum_block",
    )
    assert readiness.stale_claim_count == d("2.000000")
    assert readiness.stale_confirmation_count == d("1.000000")
    assert readiness.insufficient_quorum_count == d("1.000000")


def test_confirmation_quorum_conflict_and_latency_thresholds_apply_penalties() -> None:
    readiness = report(
        claim_input(
            "confirmation-watch",
            confirmation_age_seconds=d("43200.000000"),
        ),
        claim_input(
            "confirmation-block",
            confirmation_age_seconds=d("172801.000000"),
        ),
        claim_input("quorum-watch", corroborating_claim_count=d("2.000000")),
        claim_input("quorum-block", independent_signal_count=ZERO),
        claim_input("conflict-watch", contradiction_pressure=d("0.250000")),
        claim_input("conflict-block", contradiction_pressure=d("0.500000")),
        claim_input(
            "latency-watch",
            resolution_update_latency_seconds=d("7200.000000"),
        ),
        claim_input(
            "latency-block",
            resolution_update_latency_seconds=d("21600.000000"),
        ),
    )

    rows = {row.claim_digest: row for row in readiness.rows}
    assert rows[digest("confirmation-watch-claim")].status == "watch"
    assert "confirmation_freshness_watch" in rows[
        digest("confirmation-watch-claim")
    ].reason_codes
    assert rows[digest("confirmation-block-claim")].status == "block"
    assert "confirmation_freshness_block" in rows[
        digest("confirmation-block-claim")
    ].reason_codes
    assert rows[digest("quorum-watch-claim")].status == "watch"
    assert "corroborating_claim_quorum_watch" in rows[
        digest("quorum-watch-claim")
    ].reason_codes
    assert rows[digest("quorum-block-claim")].status == "block"
    assert "independent_signal_quorum_block" in rows[
        digest("quorum-block-claim")
    ].reason_codes
    assert rows[digest("conflict-watch-claim")].status == "watch"
    assert "contradiction_pressure_watch" in rows[
        digest("conflict-watch-claim")
    ].reason_codes
    assert rows[digest("conflict-block-claim")].status == "block"
    assert "contradiction_pressure_block" in rows[
        digest("conflict-block-claim")
    ].reason_codes
    assert rows[digest("latency-watch-claim")].status == "watch"
    assert "update_latency_watch" in rows[digest("latency-watch-claim")].reason_codes
    assert rows[digest("latency-block-claim")].status == "block"
    assert "update_latency_block" in rows[digest("latency-block-claim")].reason_codes
    assert readiness.average_freshness_decay_score == d("0.895208")
    assert readiness.contradiction_pressure_count == d("2.000000")
    assert readiness.update_latency_count == d("2.000000")


def test_public_payload_digest_validation_and_decimal_only_contract() -> None:
    payload_item = ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem(
        key="safe_context",
        value="sanitized digest claim only",
    )
    first = report(
        claim_input("zeta"),
        claim_input("alpha", claim_age_seconds=d("21600.000000")),
        payload_items=(payload_item,),
    )
    second = report(
        claim_input("alpha", claim_age_seconds=d("21600.000000")),
        claim_input("zeta"),
        payload_items=(payload_item,),
    )

    first_payload = research_event_resolution_claim_freshness_decay_ladder_public_payload(
        first,
    )
    second_payload = second.payload
    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert research_event_resolution_claim_freshness_decay_ladder_report_digest(first) == (
        first.derived_validation_digest
    )
    assert validate_research_event_resolution_claim_freshness_decay_ladder_public_payload(
        first_payload,
    ) == first_payload
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["freshness_decay_score"] == "0.970000"
    assert first_payload["rows"][1]["contradiction_pressure"] == "0.100000"
    json.dumps(first_payload, sort_keys=True)
    assert_no_float(first_payload)
    assert_no_non_decimal_public_numbers(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(first_payload)
    tampered["pass_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_event_resolution_claim_freshness_decay_ladder_public_payload(
            tampered,
        )


def test_leak_prevention_rejects_raw_identifiers_and_unsafe_public_payloads() -> None:
    with pytest.raises(ValueError, match="sha256"):
        ResearchEventResolutionClaimFreshnessDecayLadderInput(
            claim_digest="raw-candidate-id",
            resolution_digest=digest("resolution"),
            evidence_digest=digest("evidence"),
            claim_age_seconds=d("600.000000"),
            confirmation_age_seconds=d("600.000000"),
            corroborating_claim_count=d("3.000000"),
            independent_signal_count=d("2.000000"),
            contradiction_pressure=d("0.100000"),
            resolution_update_latency_seconds=d("600.000000"),
        )

    for key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem(
                key=key,
                value="safe value",
            )

    for value in (
        "https://example.test/private",
        "postgres://user:pass@example.test/db",
        "market-alpha raw locator",
        "wallet surface",
        "place order",
        "trade execution",
        "raw question text",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem(
                key="safe_key",
                value=value,
            )

    payload = report(claim_input("safe")).payload
    encoded = json.dumps(payload, sort_keys=True).lower()
    for leaked in (
        "raw-candidate-id",
        "market-alpha",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "postgres://",
        "wallet surface",
        "place order",
        "trade execution",
    ):
        assert leaked not in encoded


def test_config_flags_frozen_types_statuses_exports_and_surfaces_are_safe() -> None:
    empty = report()
    assert RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert empty.status == "block"
    assert empty.row_count == ZERO
    assert empty.reason_codes == ("empty_claim_freshness_decay_ladder_set",)
    validate_research_event_resolution_claim_freshness_decay_ladder_public_payload(
        empty.payload,
    )

    for public_dataclass in (
        ResearchEventResolutionClaimFreshnessDecayLadderConfig,
        ResearchEventResolutionClaimFreshnessDecayLadderInput,
        ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem,
        ResearchEventResolutionClaimFreshnessDecayLadderRow,
        ResearchEventResolutionClaimFreshnessDecayLadderReport,
    ):
        assert is_dataclass(public_dataclass)
        assert public_dataclass.__dataclass_params__.frozen is True

    frozen = report(claim_input("frozen"))
    with pytest.raises(FrozenInstanceError):
        frozen.status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadReport(ResearchEventResolutionClaimFreshnessDecayLadderReport):
            pass

    custom = ResearchEventResolutionClaimFreshnessDecayLadderConfig(
        min_freshness_decay_score=d("0.980000"),
    )
    readiness = report(claim_input("custom"), config=custom)
    assert readiness.status == "watch"
    assert readiness.rows[0].reason_codes == ("freshness_decay_score_watch",)

    with pytest.raises(ValueError, match="watch_claim_age_seconds"):
        ResearchEventResolutionClaimFreshnessDecayLadderConfig(
            watch_claim_age_seconds=d("86400.000000"),
            block_claim_age_seconds=d("21600.000000"),
        )
    with pytest.raises(ValueError, match="weights"):
        ResearchEventResolutionClaimFreshnessDecayLadderConfig(
            freshness_weight=d("0.500000"),
                confirmation_weight=d("0.250000"),
            quorum_weight=d("0.200000"),
            contradiction_weight=d("0.100000"),
            latency_weight=d("0.050000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventResolutionClaimFreshnessDecayLadderConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        claim_input("flags", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        claim_input("flags", readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        claim_input(contradiction_pressure=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="whole-number Decimal"):
        claim_input(corroborating_claim_count=d("1.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(report(claim_input("status")).rows[0], status="blocked")

    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_CONFIG_VERSION",
        "RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_STATUSES",
        "ResearchEventResolutionClaimFreshnessDecayLadderConfig",
        "ResearchEventResolutionClaimFreshnessDecayLadderInput",
        "ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem",
        "ResearchEventResolutionClaimFreshnessDecayLadderReport",
        "ResearchEventResolutionClaimFreshnessDecayLadderRow",
        "build_research_event_resolution_claim_freshness_decay_ladder_report",
        "research_event_resolution_claim_freshness_decay_ladder_public_payload",
        "research_event_resolution_claim_freshness_decay_ladder_report_digest",
        "validate_research_event_resolution_claim_freshness_decay_ladder_public_payload",
    )
    for public_name in api.__all__:
        assert not contains_forbidden_public_surface(public_name)

    for public_type in (
        ResearchEventResolutionClaimFreshnessDecayLadderConfig,
        ResearchEventResolutionClaimFreshnessDecayLadderInput,
        ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem,
        ResearchEventResolutionClaimFreshnessDecayLadderRow,
        ResearchEventResolutionClaimFreshnessDecayLadderReport,
    ):
        for field in fields(public_type):
            assert not contains_forbidden_public_surface(field.name)

    source = inspect.getsource(api).lower()
    tree = ast.parse(source)
    assert "float(" not in source
    assert ".total_seconds(" not in source
    for token in (
        "database",
        "network",
        "auth",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommend",
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
            "candidate_id",
            "market_id",
            "market_slug",
            "source_url",
            "source_text",
            "table_name",
        )
    ):
        return True
    tokens = tuple(token for token in lowered.replace("_", " ").split() if token)
    forbidden_tokens = frozenset(
        (
            "candidate",
            "question",
            "url",
            "text",
            "dsn",
            "table",
            "token",
            "wallet",
            "order",
            "trade",
            "auth",
            "database",
            "network",
            "live",
            "buy",
            "sell",
            "recommendation",
            "sizing",
        ),
    )
    return any(token in forbidden_tokens for token in tokens)
