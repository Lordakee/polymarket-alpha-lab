from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_scrapling_memory_claim_quorum_report as api
from polymarket_alpha_lab.research_source_scrapling_memory_claim_quorum_report import (
    ResearchSourceScraplingMemoryClaimQuorumConfig,
    ResearchSourceScraplingMemoryClaimQuorumReport,
    ResearchSourceScraplingMemoryClaimQuorumRow,
    ResearchSourceScraplingMemoryClaimSnapshot,
    build_research_source_scrapling_memory_claim_quorum_report,
    research_source_scrapling_memory_claim_quorum_public_payload,
    validate_research_source_scrapling_memory_claim_quorum_public_payload,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _snapshot(
    *,
    memo_id: str = "memo_a",
    claim_id: str = "claim_a",
    family_id: str = "family_a",
    observed_at: datetime = NOW,
    confidence_score: Decimal = Decimal("0.800000"),
    corroborates_claim: bool = True,
    conflict_flag: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceScraplingMemoryClaimSnapshot:
    return ResearchSourceScraplingMemoryClaimSnapshot(
        memo_id=memo_id,
        claim_id=claim_id,
        family_id=family_id,
        observed_at=observed_at,
        confidence_score=confidence_score,
        corroborates_claim=corroborates_claim,
        conflict_flag=conflict_flag,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    snapshots: tuple[ResearchSourceScraplingMemoryClaimSnapshot, ...],
    *,
    config: ResearchSourceScraplingMemoryClaimQuorumConfig | None = None,
) -> ResearchSourceScraplingMemoryClaimQuorumReport:
    return build_research_source_scrapling_memory_claim_quorum_report(
        snapshots,
        generated_at=NOW,
        config=config,
    )


def test_quorum_report_passes_with_corroborated_independent_memory() -> None:
    report = _report(
        (
            _snapshot(memo_id="memo_a", family_id="family_a"),
            _snapshot(memo_id="memo_b", family_id="family_b"),
            _snapshot(memo_id="memo_c", family_id="family_c"),
        ),
    )

    row = report.rows[0]
    assert report.status == "pass"
    assert report.claim_count == Decimal("1")
    assert report.pass_count == Decimal("1")
    assert row.status == "pass"
    assert row.memo_count == Decimal("3")
    assert row.family_count == Decimal("3")
    assert row.corroborating_count == Decimal("3")
    assert row.corroboration_ratio == Decimal("1.000000")
    assert row.average_confidence_score == Decimal("0.800000")
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert "claim_quorum_pass" in row.reason_codes


def test_quorum_report_uses_only_pass_watch_block_statuses() -> None:
    pass_report = _report(
        (
            _snapshot(memo_id="memo_a", family_id="family_a"),
            _snapshot(memo_id="memo_b", family_id="family_b"),
            _snapshot(memo_id="memo_c", family_id="family_c"),
        ),
    )
    watch_report = _report(
        (
            _snapshot(
                memo_id="memo_a",
                family_id="family_a",
                corroborates_claim=True,
            ),
            _snapshot(
                memo_id="memo_b",
                family_id="family_b",
                corroborates_claim=True,
            ),
            _snapshot(
                memo_id="memo_c",
                family_id="family_c",
                corroborates_claim=False,
            ),
        ),
    )
    block_report = _report((_snapshot(memo_id="memo_a", family_id="family_a"),))

    statuses = {
        pass_report.status,
        pass_report.rows[0].status,
        watch_report.status,
        watch_report.rows[0].status,
        block_report.status,
        block_report.rows[0].status,
    }
    assert statuses == {"pass", "watch", "block"}
    assert all(status in {"pass", "watch", "block"} for status in statuses)


def test_payload_is_deterministic_json_ready_and_validated_by_digest() -> None:
    snapshots = (
        _snapshot(memo_id="memo_c", family_id="family_c"),
        _snapshot(memo_id="memo_a", family_id="family_a"),
        _snapshot(memo_id="memo_b", family_id="family_b"),
    )
    same_snapshots_different_order = tuple(reversed(snapshots))

    first = _report(snapshots)
    second = _report(same_snapshots_different_order)
    first_payload = first.payload
    second_payload = second.payload

    assert first_payload == second_payload
    json.dumps(first_payload, sort_keys=True)
    assert first_payload["memo_count"] == "3"
    assert first_payload["average_confidence_score"] == "0.800000"
    assert "claim_id" not in first_payload["rows"][0]
    assert "memo_ids" not in first_payload["rows"][0]
    assert "family_ids" not in first_payload["rows"][0]
    assert len(first_payload["rows"][0]["claim_fingerprint_digest"]) == 64
    assert first_payload["rows"][0]["corroboration_ratio"] == "1.000000"
    assert first_payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first_payload["derived_validation_digest"]) == 64
    assert validate_research_source_scrapling_memory_claim_quorum_public_payload(
        first_payload,
    )
    assert (
        research_source_scrapling_memory_claim_quorum_public_payload(first)
        == first_payload
    )
    _assert_no_decimal_objects(first_payload)
    _assert_no_non_decimal_public_numbers(first)


def test_public_payload_rows_are_in_canonical_fingerprint_order() -> None:
    report = _report(
        (
            _snapshot(
                memo_id="memo_a1",
                claim_id="claim_a",
                family_id="family_a1",
            ),
            _snapshot(
                memo_id="memo_a2",
                claim_id="claim_a",
                family_id="family_a2",
            ),
            _snapshot(
                memo_id="memo_b1",
                claim_id="claim_b",
                family_id="family_b1",
            ),
            _snapshot(
                memo_id="memo_b2",
                claim_id="claim_b",
                family_id="family_b2",
            ),
        ),
    )

    payload = _mutable_payload(report)
    rows = payload["rows"]
    assert type(rows) is list
    fingerprints = [
        _first_public_row({"rows": [row]})["claim_fingerprint_digest"]
        for row in rows
    ]
    assert fingerprints == sorted(fingerprints)

    rows.reverse()
    _resign_payload(payload)
    with pytest.raises(ValueError, match="canonical order"):
        validate_research_source_scrapling_memory_claim_quorum_public_payload(payload)


def test_digest_rejects_tampered_report_and_payload() -> None:
    report = _report(
        (
            _snapshot(memo_id="memo_a", family_id="family_a"),
            _snapshot(memo_id="memo_b", family_id="family_b"),
            _snapshot(memo_id="memo_c", family_id="family_c"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = dict(report.payload)
    payload["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_source_scrapling_memory_claim_quorum_public_payload(payload)


def test_public_payload_rejects_resigned_schema_and_semantic_tampering() -> None:
    report = _report(
        (
            _snapshot(memo_id="memo_a", family_id="family_a"),
            _snapshot(memo_id="memo_b", family_id="family_b"),
            _snapshot(memo_id="memo_c", family_id="family_c"),
        ),
    )

    payload_with_extra_field = _mutable_payload(report)
    payload_with_extra_field["unexpected_field"] = "safe_value"

    payload_without_row_flag = _mutable_payload(report)
    _first_public_row(payload_without_row_flag).pop("readonly")

    payload_with_noncanonical_count = _mutable_payload(report)
    payload_with_noncanonical_count["memo_count"] = "3.0"

    payload_with_unknown_reason = _mutable_payload(report)
    _first_public_row(payload_with_unknown_reason)["reason_codes"] = [
        "unknown_reason",
    ]

    payload_with_inconsistent_count = _mutable_payload(report)
    payload_with_inconsistent_count["claim_count"] = "2"

    for payload in (
        payload_with_extra_field,
        payload_without_row_flag,
        payload_with_noncanonical_count,
        payload_with_unknown_reason,
        payload_with_inconsistent_count,
    ):
        _resign_payload(payload)
        with pytest.raises(ValueError):
            validate_research_source_scrapling_memory_claim_quorum_public_payload(
                payload,
            )


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report(
        (
            _snapshot(memo_id="memo_a", family_id="family_a"),
            _snapshot(memo_id="memo_b", family_id="family_b"),
            _snapshot(memo_id="memo_c", family_id="family_c"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceScraplingMemoryClaimQuorumConfig):
            pass


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceScraplingMemoryClaimQuorumConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _snapshot(report_only=False)  # type: ignore[call-arg]

    report = _report(
        (
            _snapshot(memo_id="memo_a", family_id="family_a"),
            _snapshot(memo_id="memo_b", family_id="family_b"),
            _snapshot(memo_id="memo_c", family_id="family_c"),
        ),
    )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_decimal_only_inputs_are_required() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceScraplingMemoryClaimQuorumConfig(
            min_memo_count=2,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Decimal"):
        _snapshot(confidence_score=0.8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceScraplingMemoryClaimQuorumRow(
            claim_id="claim_a",
            memo_count=Decimal("1"),
            family_count=Decimal("1"),
            corroborating_count=Decimal("1"),
            conflict_count=Decimal("0"),
            corroboration_ratio=Decimal("1.000000"),
            conflict_ratio=Decimal("0.000000"),
            average_confidence_score=0.8,  # type: ignore[arg-type]
            oldest_memory_age_seconds=Decimal("0.000000"),
            status="pass",
            reason_codes=("claim_quorum_pass",),
            memo_ids=("memo_a",),
            family_ids=("family_a",),
        )


def test_row_rejects_more_families_than_memos() -> None:
    with pytest.raises(ValueError, match="family_count"):
        ResearchSourceScraplingMemoryClaimQuorumRow(
            claim_id="claim_a",
            memo_count=Decimal("1"),
            family_count=Decimal("2"),
            corroborating_count=Decimal("1"),
            conflict_count=Decimal("0"),
            corroboration_ratio=Decimal("1.000000"),
            conflict_ratio=Decimal("0.000000"),
            average_confidence_score=Decimal("0.800000"),
            oldest_memory_age_seconds=Decimal("0.000000"),
            status="pass",
            reason_codes=("claim_quorum_pass",),
            memo_ids=("memo_a",),
            family_ids=("family_a", "family_b"),
        )


def test_row_rejects_report_only_empty_reason_code() -> None:
    with pytest.raises(ValueError, match="empty"):
        ResearchSourceScraplingMemoryClaimQuorumRow(
            claim_id="claim_a",
            memo_count=Decimal("1"),
            family_count=Decimal("1"),
            corroborating_count=Decimal("0"),
            conflict_count=Decimal("0"),
            corroboration_ratio=Decimal("0.000000"),
            conflict_ratio=Decimal("0.000000"),
            average_confidence_score=Decimal("0.800000"),
            oldest_memory_age_seconds=Decimal("0.000000"),
            status="block",
            reason_codes=("empty_memory_claim_quorum",),
            memo_ids=("memo_a",),
            family_ids=("family_a",),
        )


def test_unsafe_public_material_is_rejected_and_not_leaked() -> None:
    unsafe_values = (
        "https://example.invalid/path",
        "raw candidate note",
        "market description",
        "source url",
        "source text",
        "postgres dsn",
        "table name",
        "token value",
        "network request",
        "wallet action",
        "auth secret",
        "order intent",
        "live trading",
        "trade identifier",
        "execution request",
        "sourceText body",
        "sizing advice",
        "recommendation",
    )
    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            _snapshot(memo_id=value)

    report = _report(
        (
            _snapshot(memo_id="memo_a", family_id="family_a"),
            _snapshot(memo_id="memo_b", family_id="family_b"),
            _snapshot(memo_id="memo_c", family_id="family_c"),
        ),
    )
    payload_json = json.dumps(report.payload, sort_keys=True).lower()
    for forbidden in (
        "candidate",
        "market",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "network",
        "wallet",
        "auth",
        "order",
        "trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in payload_json
    _assert_public_strings_exclude(
        report.payload,
        (
            "memo_a",
            "memo_b",
            "memo_c",
            "claim_a",
            "family_a",
            "family_b",
            "family_c",
        ),
    )


def test_no_forbidden_runtime_capabilities_are_exposed() -> None:
    forbidden_public_terms = (
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_terms)

    for cls in (
        ResearchSourceScraplingMemoryClaimQuorumConfig,
        ResearchSourceScraplingMemoryClaimSnapshot,
        ResearchSourceScraplingMemoryClaimQuorumRow,
        ResearchSourceScraplingMemoryClaimQuorumReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_public_terms)

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


def test_future_observations_are_rejected() -> None:
    with pytest.raises(ValueError, match="observed_at"):
        _report((_snapshot(observed_at=NOW + timedelta(seconds=1)),))


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _mutable_payload(
    report: ResearchSourceScraplingMemoryClaimQuorumReport,
) -> dict[str, object]:
    value = json.loads(json.dumps(report.payload))
    assert type(value) is dict
    return value


def _first_public_row(payload: dict[str, object]) -> dict[str, object]:
    rows = payload["rows"]
    assert type(rows) is list
    assert rows
    row = rows[0]
    assert type(row) is dict
    return row


def _resign_payload(payload: dict[str, object]) -> None:
    payload["derived_validation_digest"] = api._derived_validation_digest(payload)


def _assert_public_strings_exclude(
    value: object,
    forbidden_values: tuple[str, ...],
) -> None:
    if isinstance(value, str):
        assert value not in forbidden_values
        return
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_strings_exclude(item, forbidden_values)
    if isinstance(value, list):
        for item in value:
            _assert_public_strings_exclude(item, forbidden_values)


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
