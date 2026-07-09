from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json

import pytest

import polymarket_alpha_lab.research_strategy_evidence_authority_conflict_decay_report as api
from polymarket_alpha_lab.research_strategy_evidence_authority_conflict_decay_report import (
    ResearchStrategyEvidenceAuthorityConflictDecayConfig,
    ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem,
    ResearchStrategyEvidenceAuthorityConflictDecayReport,
    ResearchStrategyEvidenceAuthorityConflictDecayRow,
    ResearchStrategyEvidenceAuthorityConflictDecaySignal,
    build_research_strategy_evidence_authority_conflict_decay_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)
CANDIDATE_A = "a" * 64
CANDIDATE_B = "b" * 64
EVIDENCE_A = "1" * 64
EVIDENCE_B = "2" * 64
EVIDENCE_C = "3" * 64


def _signal(
    *,
    candidate_digest: str = CANDIDATE_A,
    evidence_digest: str = EVIDENCE_A,
    evidence_family: str = "official",
    observed_at: datetime = NOW,
    authority_score: Decimal = Decimal("0.900000"),
    conflict_score: Decimal = Decimal("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyEvidenceAuthorityConflictDecaySignal:
    return ResearchStrategyEvidenceAuthorityConflictDecaySignal(
        candidate_digest=candidate_digest,
        evidence_digest=evidence_digest,
        evidence_family=evidence_family,
        observed_at=observed_at,
        authority_score=authority_score,
        conflict_score=conflict_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    signals: tuple[ResearchStrategyEvidenceAuthorityConflictDecaySignal, ...],
    *,
    config: ResearchStrategyEvidenceAuthorityConflictDecayConfig | None = None,
    public_payload: tuple[
        ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem,
        ...,
    ] = (),
) -> ResearchStrategyEvidenceAuthorityConflictDecayReport:
    return build_research_strategy_evidence_authority_conflict_decay_report(
        signals,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_fresh_authoritative_low_conflict_evidence_passes() -> None:
    report = _report(
        (
            _signal(
                evidence_digest=EVIDENCE_A,
                evidence_family="official",
                authority_score=Decimal("0.900000"),
                conflict_score=Decimal("0.100000"),
            ),
            _signal(
                evidence_digest=EVIDENCE_B,
                evidence_family="primary",
                authority_score=Decimal("0.800000"),
                conflict_score=Decimal("0.000000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "pass"
    assert report.candidate_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert row.evidence_count == Decimal("2.000000")
    assert row.evidence_family_count == Decimal("2.000000")
    assert row.average_authority_score == Decimal("0.850000")
    assert row.max_conflict_score == Decimal("0.100000")
    assert row.average_decay_score == Decimal("1.000000")
    assert row.authority_conflict_decay_score == Decimal("0.765000")
    assert row.status == "pass"
    assert "authority_conflict_decay_pass" in row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_high_conflict_blocks_even_when_authority_is_high() -> None:
    report = _report(
        (
            _signal(
                evidence_digest=EVIDENCE_A,
                evidence_family="official",
                authority_score=Decimal("0.950000"),
                conflict_score=Decimal("0.900000"),
            ),
            _signal(
                evidence_digest=EVIDENCE_B,
                evidence_family="primary",
                authority_score=Decimal("0.900000"),
                conflict_score=Decimal("0.850000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "block"
    assert report.block_count == Decimal("1.000000")
    assert row.max_conflict_score == Decimal("0.900000")
    assert row.status == "block"
    assert "conflict_block" in row.reason_codes


def test_decay_can_demote_authoritative_evidence_to_watch() -> None:
    report = _report(
        (
            _signal(
                observed_at=NOW - timedelta(seconds=1800),
                authority_score=Decimal("0.800000"),
                conflict_score=Decimal("0.000000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "watch"
    assert row.average_decay_score == Decimal("0.500000")
    assert row.authority_conflict_decay_score == Decimal("0.400000")
    assert row.status == "watch"
    assert "decay_watch" in row.reason_codes


def test_payload_is_deterministic_json_ready_and_digest_validated() -> None:
    signal_a = _signal(
        candidate_digest=CANDIDATE_A,
        evidence_digest=EVIDENCE_A,
        evidence_family="official",
    )
    signal_b = _signal(
        candidate_digest=CANDIDATE_A,
        evidence_digest=EVIDENCE_B,
        evidence_family="primary",
        authority_score=Decimal("0.800000"),
        conflict_score=Decimal("0.000000"),
    )
    payload_a = ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
        "cycle_label",
        "cycle alpha",
    )
    payload_b = ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
        "scope_label",
        "paper report",
    )

    report = _report((signal_b, signal_a), public_payload=(payload_b, payload_a))
    same_report = _report((signal_a, signal_b), public_payload=(payload_a, payload_b))

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload == same_report.payload
    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["authority_conflict_decay_score"] == "0.765000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_public_payload_api_validates_schema_and_canonical_digest() -> None:
    report = _report(
        (
            _signal(evidence_digest=EVIDENCE_A, evidence_family="official"),
            _signal(evidence_digest=EVIDENCE_B, evidence_family="primary"),
        ),
        public_payload=(
            ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
                "cycle_label",
                "cycle alpha",
            ),
        ),
    )

    payload = api.research_strategy_evidence_authority_conflict_decay_report_payload(
        report,
    )

    assert payload == report.payload
    assert (
        api.validate_research_strategy_evidence_authority_conflict_decay_report_payload(
            payload,
        )
        is True
    )
    assert payload["derived_validation_digest"] == _canonical_payload_digest(payload)


def test_public_payload_validator_rejects_schema_and_type_tampering() -> None:
    report = _report(
        (
            _signal(evidence_digest=EVIDENCE_A, evidence_family="official"),
            _signal(evidence_digest=EVIDENCE_B, evidence_family="primary"),
        ),
        public_payload=(
            ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
                "cycle_label",
                "cycle alpha",
            ),
        ),
    )
    payload = report.payload

    extra_key = dict(payload)
    extra_key["extra"] = "value"
    _rehash_payload(extra_key)
    with pytest.raises(ValueError, match="payload keys"):
        api.validate_research_strategy_evidence_authority_conflict_decay_report_payload(
            extra_key,
        )

    missing_key = dict(payload)
    missing_key.pop("reason_codes")
    _rehash_payload(missing_key)
    with pytest.raises(ValueError, match="payload keys"):
        api.validate_research_strategy_evidence_authority_conflict_decay_report_payload(
            missing_key,
        )

    bad_row = json.loads(json.dumps(payload))
    bad_row["rows"][0]["extra"] = "value"
    _rehash_payload(bad_row)
    with pytest.raises(ValueError, match="row keys"):
        api.validate_research_strategy_evidence_authority_conflict_decay_report_payload(
            bad_row,
        )

    bad_item = json.loads(json.dumps(payload))
    bad_item["public_payload"][0]["extra"] = "value"
    _rehash_payload(bad_item)
    with pytest.raises(ValueError, match="public payload item keys"):
        api.validate_research_strategy_evidence_authority_conflict_decay_report_payload(
            bad_item,
        )

    noncanonical_count = dict(payload)
    noncanonical_count["candidate_count"] = "1.0"
    _rehash_payload(noncanonical_count)
    with pytest.raises(ValueError, match="candidate_count"):
        api.validate_research_strategy_evidence_authority_conflict_decay_report_payload(
            noncanonical_count,
        )

    wrong_type = dict(payload)
    wrong_type["candidate_count"] = 1
    _rehash_payload(wrong_type)
    with pytest.raises(ValueError, match="candidate_count"):
        api.validate_research_strategy_evidence_authority_conflict_decay_report_payload(
            wrong_type,
        )


def test_dataclasses_are_frozen_final_and_decimal_counts_are_integral() -> None:
    report = _report(
        (
            _signal(evidence_digest=EVIDENCE_A, evidence_family="official"),
            _signal(evidence_digest=EVIDENCE_B, evidence_family="primary"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    for dataclass_type in (
        ResearchStrategyEvidenceAuthorityConflictDecayConfig,
        ResearchStrategyEvidenceAuthorityConflictDecaySignal,
        ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem,
        ResearchStrategyEvidenceAuthorityConflictDecayRow,
        ResearchStrategyEvidenceAuthorityConflictDecayReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type("UnsafeSubclass", (dataclass_type,), {})

    with pytest.raises(ValueError, match="integral"):
        ResearchStrategyEvidenceAuthorityConflictDecayConfig(
            min_evidence_family_count=Decimal("1.500000"),
        )

    with pytest.raises(ValueError, match="integral"):
        ResearchStrategyEvidenceAuthorityConflictDecayConfig(
            min_evidence_family_count=Decimal("1.0000004"),
        )

    with pytest.raises(ValueError, match="integral"):
        replace(report.rows[0], evidence_count=Decimal("2.500000"))


def test_duplicate_evidence_and_public_payload_keys_are_rejected() -> None:
    duplicate_signal = _signal(
        evidence_digest=EVIDENCE_A,
        evidence_family="primary",
    )
    with pytest.raises(ValueError, match="signals must be unique"):
        _report((_signal(), duplicate_signal))

    duplicate_key = (
        ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
            "cycle_label",
            "cycle alpha",
        ),
        ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
            "cycle_label",
            "cycle beta",
        ),
    )
    with pytest.raises(ValueError, match="public_payload keys must be unique"):
        _report((_signal(),), public_payload=duplicate_key)


def test_hard_flags_and_digest_tampering_are_rejected() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategyEvidenceAuthorityConflictDecayConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _signal(report_only=False)  # type: ignore[call-arg]

    report = _report(
        (
            _signal(evidence_digest=EVIDENCE_A, evidence_family="official"),
            _signal(evidence_digest=EVIDENCE_B, evidence_family="primary"),
        ),
    )

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
                    "cycle_label",
                    "changed",
                ),
            ),
        )


def test_statuses_are_limited_to_pass_watch_block() -> None:
    report = _report(
        (
            _signal(evidence_digest=EVIDENCE_A, evidence_family="official"),
            _signal(evidence_digest=EVIDENCE_B, evidence_family="primary"),
        ),
    )

    assert {report.status, *(row.status for row in report.rows)} <= {
        "pass",
        "watch",
        "block",
    }

    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")


def test_unsafe_public_payload_and_raw_identifier_surfaces_are_rejected() -> None:
    for key in (
        "candidate_id",
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet_key",
        "order_key",
        "trade_key",
        "sizing_key",
        "recommendation_key",
        "live_key",
        "network_key",
        "auth_key",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
                key,
                "safe value",
            )

    for value in (
        "https://example.test/source",
        "candidate_id=candidate-alpha",
        "market_slug=will-event-happen",
        "question=Will this happen?",
        "source_text=raw evidence",
        "dsn=postgres://example",
        "wallet surface",
        "order surface",
        "trade surface",
        "position sizing",
        "recommendation surface",
        "auth token",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
                "safe_key",
                value,
            )

    with pytest.raises(ValueError, match="candidate_digest"):
        _signal(candidate_digest="candidate-alpha")

    with pytest.raises(ValueError, match="evidence_digest"):
        _signal(evidence_digest="source-url-raw")


def test_no_unsafe_public_surfaces_are_exposed() -> None:
    forbidden_public_name_parts = (
        "candidate_id",
        "raw_candidate",
        "market",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "network",
        "live",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_name_parts)

    for cls in (
        ResearchStrategyEvidenceAuthorityConflictDecayConfig,
        ResearchStrategyEvidenceAuthorityConflictDecaySignal,
        ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem,
        ResearchStrategyEvidenceAuthorityConflictDecayRow,
        ResearchStrategyEvidenceAuthorityConflictDecayReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_public_name_parts)

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


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _canonical_payload_digest(payload: dict[str, object]) -> str:
    digest_values = dict(payload)
    digest_values.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _rehash_payload(payload: dict[str, object]) -> None:
    payload["derived_validation_digest"] = _canonical_payload_digest(payload)


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
