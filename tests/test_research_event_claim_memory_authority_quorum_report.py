from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

import pytest

import polymarket_alpha_lab.research_event_claim_memory_authority_quorum_report as api
from polymarket_alpha_lab.research_event_claim_memory_authority_quorum_report import (
    ResearchEventClaimMemoryAuthorityObservation,
    ResearchEventClaimMemoryAuthorityQuorumConfig,
    ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem,
    ResearchEventClaimMemoryAuthorityQuorumReport,
    ResearchEventClaimMemoryAuthorityQuorumRow,
    build_research_event_claim_memory_authority_quorum_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _observation(
    *,
    event_id: str = "event_alpha",
    claim_id: str = "claim_alpha",
    memory_ref: str = "memory_alpha",
    authority_ref: str = "authority_alpha",
    memory_score: Decimal = Decimal("0.800000"),
    authority_score: Decimal = Decimal("0.900000"),
    supports_claim: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventClaimMemoryAuthorityObservation:
    return ResearchEventClaimMemoryAuthorityObservation(
        event_id=event_id,
        claim_id=claim_id,
        memory_ref=memory_ref,
        authority_ref=authority_ref,
        recorded_at=NOW,
        memory_score=memory_score,
        authority_score=authority_score,
        supports_claim=supports_claim,
        private_material=(
            "CANDIDATE-SECRET-001",
            "MARKET-SECRET-001",
            "https://private.example/claim",
            "raw claim text must stay private",
            "postgres://private-dsn",
            "private_claim_table",
            "private-token",
        ),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    observations: tuple[ResearchEventClaimMemoryAuthorityObservation, ...],
    *,
    public_payload: tuple[
        ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem,
        ...,
    ] = (),
    config: ResearchEventClaimMemoryAuthorityQuorumConfig | None = None,
) -> ResearchEventClaimMemoryAuthorityQuorumReport:
    return build_research_event_claim_memory_authority_quorum_report(
        observations,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_pass_status_requires_memory_authority_quorum() -> None:
    report = _report(
        (
            _observation(memory_ref="memory_a", authority_ref="authority_a"),
            _observation(memory_ref="memory_b", authority_ref="authority_b"),
        ),
    )

    row = report.rows[0]
    assert report.status == "pass"
    assert report.event_claim_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert row.observation_count == Decimal("2.000000")
    assert row.supporting_memory_count == Decimal("2.000000")
    assert row.supporting_authority_count == Decimal("2.000000")
    assert row.status == "pass"
    assert row.quorum_score == Decimal("0.850000")
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_statuses_are_limited_to_pass_watch_block() -> None:
    report = _report(
        (
            _observation(
                event_id="event_watch",
                claim_id="claim_watch",
                memory_ref="memory_a",
                authority_ref="authority_a",
                memory_score=Decimal("0.500000"),
                authority_score=Decimal("0.500000"),
            ),
            _observation(
                event_id="event_watch",
                claim_id="claim_watch",
                memory_ref="memory_b",
                authority_ref="authority_b",
                memory_score=Decimal("0.500000"),
                authority_score=Decimal("0.500000"),
            ),
            _observation(event_id="event_block", claim_id="claim_block"),
        ),
    )

    assert report.status == "block"
    assert {row.status for row in report.rows} == {"watch", "block"}
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")

    row = report.rows[0]
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")


def test_public_payload_is_canonical_decimal_only_and_digest_checked() -> None:
    observations = (
        _observation(memory_ref="memory_b", authority_ref="authority_b"),
        _observation(memory_ref="memory_a", authority_ref="authority_a"),
    )
    report = _report(
        observations,
        public_payload=(
            ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem(
                key="review_scope",
                value="event_claim_quorum",
            ),
        ),
    )
    same_report = _report(tuple(reversed(observations)), public_payload=report.public_payload)

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload == same_report.payload
    assert payload["event_claim_count"] == "1.000000"
    assert payload["average_quorum_score"] == "0.850000"
    assert payload["rows"][0]["quorum_score"] == "0.850000"
    assert payload["derived_validation_digest"] == _canonical_digest(payload)
    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)
    _assert_no_private_raw_leaks(payload)


def test_public_rows_use_digest_not_raw_event_or_claim_ids() -> None:
    report = _report(
        (
            _observation(memory_ref="memory_a", authority_ref="authority_a"),
            _observation(memory_ref="memory_b", authority_ref="authority_b"),
        ),
    )

    row = report.rows[0]
    payload_row = report.payload["rows"][0]
    serialized = json.dumps(report.payload, sort_keys=True).lower()

    assert not hasattr(row, "event_id")
    assert not hasattr(row, "claim_id")
    assert row.event_claim_digest == payload_row["event_claim_digest"]
    assert isinstance(row.event_claim_digest, str)
    assert len(row.event_claim_digest) == 64
    assert "event_id" not in payload_row
    assert "claim_id" not in payload_row
    assert "event_alpha" not in serialized
    assert "claim_alpha" not in serialized


def test_digest_tampering_is_rejected() -> None:
    report = _report(
        (
            _observation(memory_ref="memory_a", authority_ref="authority_a"),
            _observation(memory_ref="memory_b", authority_ref="authority_b"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem(
                    key="review_scope",
                    value="changed",
                ),
            ),
        )


def test_dataclasses_are_frozen_and_reject_subclassing_and_non_decimal_numbers() -> None:
    report = _report(
        (
            _observation(memory_ref="memory_a", authority_ref="authority_a"),
            _observation(memory_ref="memory_b", authority_ref="authority_b"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchEventClaimMemoryAuthorityQuorumConfig):
            pass

    with pytest.raises(ValueError, match="Decimal"):
        ResearchEventClaimMemoryAuthorityQuorumConfig(min_memory_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        _observation(memory_score=1)  # type: ignore[arg-type]


def test_safety_flags_and_public_payload_guards() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventClaimMemoryAuthorityQuorumConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _observation(report_only=False)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="readonly"):
        ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem(
            key="review_scope",
            value="event_claim_quorum",
            readonly=False,
        )

    for key in (
        "db_key",
        "network_key",
        "wallet_key",
        "auth_key",
        "order_key",
        "live_key",
        "trading_key",
        "sizing_key",
        "recommendation_key",
        "candidate_key",
        "market_key",
        "source_key",
        "url_key",
        "dsn_key",
        "table_key",
        "token_key",
        "slug_key",
        "question_key",
        "trade_key",
        "id_key",
    ):
        with pytest.raises(ValueError, match="public payload"):
            ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem(key, "safe")

    for value in (
        "db value",
        "network value",
        "wallet value",
        "auth value",
        "order value",
        "live value",
        "trading value",
        "sizing value",
        "recommendation value",
        "candidate value",
        "market value",
        "source value",
        "url value",
        "dsn value",
        "table value",
        "token value",
        "slug value",
        "question value",
        "trade value",
        "id value",
    ):
        with pytest.raises(ValueError, match="public payload"):
            ResearchEventClaimMemoryAuthorityQuorumPublicPayloadItem("review_scope", value)

    for public_name in api.__all__:
        assert "wallet" not in public_name.lower()
        assert "order" not in public_name.lower()


def _canonical_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def _assert_no_private_raw_leaks(payload: object) -> None:
    serialized = json.dumps(payload, sort_keys=True).lower()
    for private_value in (
        "candidate-secret-001",
        "market-secret-001",
        "private.example",
        "raw claim text",
        "private-dsn",
        "private_claim_table",
        "private-token",
    ):
        assert private_value not in serialized
    for private_key in (
        "candidate",
        "market",
        "source",
        "url",
        "dsn",
        "table",
        "token",
    ):
        assert private_key not in serialized
