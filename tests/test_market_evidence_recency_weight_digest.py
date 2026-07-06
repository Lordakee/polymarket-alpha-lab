from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_evidence_recency_weight_digest import (
    MarketEvidenceRecencyWeightConfig,
    MarketEvidenceRecencyWeightDigest,
    MarketEvidenceRecencyWeightObservation,
    MarketEvidenceRecencyWeightReasonCodeCount,
    MarketEvidenceRecencyWeightRow,
    build_market_evidence_recency_weight_digest,
    market_evidence_recency_weight_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


@dataclass(frozen=True)
class SuppliedEvidenceShape:
    market_slug: str
    evidence_id: str
    source_id: str
    source_family: str
    source_reliability_weight: Decimal
    evidence_observed_at: datetime
    supports_outcome: str
    contradicts_current_summary: bool
    reference: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketEvidenceRecencyWeightConfig:
    values = {
        "config_version": "market-evidence-recency-weight-digest-v0",
        "fresh_age_seconds": d("3600"),
        "stale_age_seconds": d("86400"),
        "min_source_reliability_weight": d("0.250000"),
        "min_weighted_freshness_score": d("0.700000"),
    }
    values.update(overrides)
    return MarketEvidenceRecencyWeightConfig(**values)


def evidence(
    index: int,
    *,
    market_slug: str = "btc-above-100k",
    source_family: str = "official_resolution",
    source_reliability_weight: Decimal = d("1.000000"),
    evidence_observed_at: datetime | None = None,
    supports_outcome: str = "yes",
    contradicts_current_summary: bool = False,
    reference: str | None = None,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketEvidenceRecencyWeightObservation:
    return MarketEvidenceRecencyWeightObservation(
        market_slug=market_slug,
        evidence_id=f"evidence-{index:03d}",
        source_id=f"source-{index:03d}",
        source_family=source_family,
        source_reliability_weight=source_reliability_weight,
        evidence_observed_at=(
            evidence_observed_at
            if evidence_observed_at is not None
            else GENERATED_AT - timedelta(minutes=30)
        ),
        supports_outcome=supports_outcome,
        contradicts_current_summary=contradicts_current_summary,
        reference=(
            reference
            if reference is not None
            else f"https://example.test/research/{index}?token=secret-value"
        ),
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    observations: tuple[object, ...],
    *,
    cfg: MarketEvidenceRecencyWeightConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketEvidenceRecencyWeightDigest:
    return build_market_evidence_recency_weight_digest(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_zero_digest() -> None:
    report = digest(())

    assert type(report) is MarketEvidenceRecencyWeightDigest
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-evidence-recency-weight-digest-v0"
    assert report.market_count == d("0")
    assert report.evidence_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.stale_evidence_count == d("0")
    assert report.contradiction_count == d("0")
    assert report.average_weighted_freshness_score is None
    assert report.status == "blocked"
    assert report.reason_codes == ("no_market_evidence",)
    assert report.rows == ()
    assert report.reason_code_counts == (
        MarketEvidenceRecencyWeightReasonCodeCount(
            reason_code="no_market_evidence",
            count=d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_fresh_reliable_evidence_passes_with_weighted_score_and_redacted_reference() -> None:
    report = digest(
        (
            evidence(2, source_reliability_weight=d("0.500000")),
            evidence(
                1,
                evidence_observed_at=datetime(
                    2026,
                    7,
                    2,
                    7,
                    45,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                source_reliability_weight=d("1.000000"),
                reference="https://source.example/path?api_key=super-secret",
            ),
        ),
    )

    assert report.status == "pass"
    assert report.reason_codes == ("evidence_recency_weight_pass",)
    assert report.market_count == d("1")
    assert report.evidence_count == d("2")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.stale_evidence_count == d("0")
    assert report.contradiction_count == d("0")
    assert report.average_weighted_freshness_score == d("1.000000")

    row = report.rows[0]
    assert type(row) is MarketEvidenceRecencyWeightRow
    assert row.market_slug == "btc-above-100k"
    assert row.latest_evidence_observed_at == GENERATED_AT - timedelta(minutes=15)
    assert row.latest_evidence_age_seconds == d("900")
    assert row.evidence_count == d("2")
    assert row.source_count == d("2")
    assert row.latest_source_reliability_weight == d("1.000000")
    assert row.average_source_reliability_weight == d("0.750000")
    assert row.stale_evidence_count == d("0")
    assert row.contradiction_count == d("0")
    assert row.weighted_freshness_score == d("1.000000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "evidence_recency_weight_pass",
        "evidence_recent",
        "no_contradictions",
        "reliable_sources",
    )
    assert row.evidence_ids == ("evidence-001", "evidence-002")
    assert row.redacted_references == ("[redacted_reference]",)


def test_stale_low_reliability_and_contradiction_watch_market() -> None:
    report = digest(
        (
            evidence(
                1,
                source_reliability_weight=d("0.200000"),
                evidence_observed_at=GENERATED_AT - timedelta(days=2),
                contradicts_current_summary=True,
                supports_outcome="no",
                reason_codes=("manual_review",),
            ),
            evidence(
                2,
                source_reliability_weight=d("0.250000"),
                evidence_observed_at=GENERATED_AT - timedelta(hours=12),
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "watch"
    assert report.watch_count == d("1")
    assert report.stale_evidence_count == d("1")
    assert report.contradiction_count == d("1")
    assert row.latest_evidence_age_seconds == d("43200")
    assert row.stale_evidence_count == d("1")
    assert row.contradiction_count == d("1")
    assert row.latest_source_reliability_weight == d("0.250000")
    assert row.average_source_reliability_weight == d("0.225000")
    assert row.weighted_freshness_score == d("0.087500")
    assert row.status == "watch"
    assert row.reason_codes == (
        "contradiction_present",
        "evidence_recency_weight_watch",
        "evidence_stale",
        "input_manual_review",
        "low_source_reliability",
    )
    assert report.reason_code_counts == (
        MarketEvidenceRecencyWeightReasonCodeCount(
            reason_code="contradiction_present",
            count=d("1"),
        ),
        MarketEvidenceRecencyWeightReasonCodeCount(
            reason_code="evidence_recency_weight_watch",
            count=d("1"),
        ),
        MarketEvidenceRecencyWeightReasonCodeCount(
            reason_code="evidence_stale",
            count=d("1"),
        ),
        MarketEvidenceRecencyWeightReasonCodeCount(
            reason_code="input_manual_review",
            count=d("1"),
        ),
        MarketEvidenceRecencyWeightReasonCodeCount(
            reason_code="low_source_reliability",
            count=d("1"),
        ),
    )


def test_no_evidence_for_market_shape_blocks_row() -> None:
    report = digest(
        (
            SuppliedEvidenceShape(
                market_slug="empty-market",
                evidence_id="",
                source_id="",
                source_family="",
                source_reliability_weight=d("0"),
                evidence_observed_at=GENERATED_AT,
                supports_outcome="unknown",
                contradicts_current_summary=False,
                reference="",
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "blocked"
    assert row.market_slug == "empty-market"
    assert row.evidence_count == d("0")
    assert row.source_count == d("0")
    assert row.latest_evidence_observed_at is None
    assert row.latest_evidence_age_seconds is None
    assert row.latest_source_reliability_weight is None
    assert row.average_source_reliability_weight is None
    assert row.weighted_freshness_score == d("0.000000")
    assert row.status == "blocked"
    assert row.reason_codes == ("missing_market_evidence",)


def test_rows_and_reasons_sort_deterministically() -> None:
    report = digest(
        (
            evidence(
                3,
                market_slug="z-market",
                source_reliability_weight=d("0.250000"),
                evidence_observed_at=GENERATED_AT - timedelta(days=2),
            ),
            evidence(
                1,
                market_slug="a-market",
                source_reliability_weight=d("1.000000"),
                reason_codes=("zeta", "alpha"),
            ),
            evidence(
                2,
                market_slug="z-market",
                source_reliability_weight=d("0.500000"),
                reason_codes=("alpha",),
            ),
        ),
    )

    assert tuple(row.market_slug for row in report.rows) == ("a-market", "z-market")
    assert report.rows[0].reason_codes == (
        "evidence_recency_weight_pass",
        "evidence_recent",
        "input_alpha",
        "input_zeta",
        "no_contradictions",
        "reliable_sources",
    )
    assert report.rows[1].evidence_ids == ("evidence-002", "evidence-003")
    assert report.reason_codes == (
        "evidence_recency_weight_pass",
        "evidence_recency_weight_watch",
        "evidence_stale",
        "input_alpha",
        "input_zeta",
        "low_source_reliability",
        "no_contradictions",
        "reliable_sources",
    )


def test_payload_uses_decimal_strings_utc_datetimes_and_no_float_values() -> None:
    report = digest(
        (
            evidence(1),
            evidence(2, market_slug="z-market", evidence_observed_at=GENERATED_AT),
        ),
    )

    payload = market_evidence_recency_weight_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["market_count"] == "2"
    assert payload["average_weighted_freshness_score"] == "1.000000"
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["rows"][0]["latest_evidence_age_seconds"] == "1800"
    assert payload["rows"][1]["latest_evidence_age_seconds"] == "0"
    assert "2.0" not in encoded
    assert "secret" not in encoded.lower()
    assert "token" not in encoded.lower()
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_derived_validation_digest_is_report_and_row_bound() -> None:
    report = digest((evidence(1), evidence(2, market_slug="z-market")))
    payload = market_evidence_recency_weight_digest_payload(report)

    assert type(report.derived_validation_digest) is str
    assert len(report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in report.derived_validation_digest
    )
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert all(
        character in "0123456789abcdef"
        for row in report.rows
        for character in row.derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["derived_validation_digest"] == (
        report.rows[0].derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.rows[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_payload_revalidates_decimal_strings_flags_and_derived_digest() -> None:
    report = digest((evidence(1),))
    payload = market_evidence_recency_weight_digest_payload(report)

    assert market_evidence_recency_weight_digest_payload(payload) == payload
    assert not any(
        type(value) in (Decimal, int, float)
        for value in _walk_payload_values(payload)
    )

    numeric_payload = json.loads(json.dumps(payload))
    numeric_payload["market_count"] = 1
    with pytest.raises(ValueError, match="market_count"):
        market_evidence_recency_weight_digest_payload(numeric_payload)

    row_numeric_payload = json.loads(json.dumps(payload))
    row_numeric_payload["rows"][0]["weighted_freshness_score"] = 1.0
    with pytest.raises(ValueError, match="weighted_freshness_score"):
        market_evidence_recency_weight_digest_payload(row_numeric_payload)

    downgraded_payload = json.loads(json.dumps(payload))
    downgraded_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        market_evidence_recency_weight_digest_payload(downgraded_payload)

    missing_digest_payload = json.loads(json.dumps(payload))
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_evidence_recency_weight_digest_payload(missing_digest_payload)

    tampered_payload = json.loads(json.dumps(payload))
    tampered_payload["market_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_evidence_recency_weight_digest_payload(tampered_payload)


def test_inputs_and_public_payload_reject_unsafe_surfaces() -> None:
    bad_text = "market-live-auth-wallet-order-network-database-persist"

    for field_name in ("market_slug", "source_family", "supports_outcome"):
        with pytest.raises(ValueError, match=field_name):
            evidence(1, **{field_name: bad_text})

    with pytest.raises(ValueError, match="evidence_id"):
        MarketEvidenceRecencyWeightObservation(
            market_slug="btc-above-100k",
            evidence_id=bad_text,
            source_id="source-001",
            source_family="official_resolution",
            source_reliability_weight=d("1.000000"),
            evidence_observed_at=GENERATED_AT,
            supports_outcome="yes",
            contradicts_current_summary=False,
            reference="",
        )
    with pytest.raises(ValueError, match="source_id"):
        MarketEvidenceRecencyWeightObservation(
            market_slug="btc-above-100k",
            evidence_id="evidence-001",
            source_id=bad_text,
            source_family="official_resolution",
            source_reliability_weight=d("1.000000"),
            evidence_observed_at=GENERATED_AT,
            supports_outcome="yes",
            contradicts_current_summary=False,
            reference="",
        )
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("live_order",))

    payload = market_evidence_recency_weight_digest_payload(digest((evidence(1),)))
    unsafe_payload = json.loads(json.dumps(payload))
    unsafe_payload["unsafe_order_key"] = "value"
    with pytest.raises(ValueError, match="unsafe"):
        market_evidence_recency_weight_digest_payload(unsafe_payload)


def test_observation_reference_is_redacted_before_repr_and_payload() -> None:
    observation = evidence(
        1,
        reference="https://source.example/path?api_key=super-secret&session=abc123",
    )

    assert observation.reference == "[redacted_reference]"
    encoded_observation = repr(observation).lower()
    assert "api_key" not in encoded_observation
    assert "super-secret" not in encoded_observation
    assert "session" not in encoded_observation
    assert "abc123" not in encoded_observation

    payload = market_evidence_recency_weight_digest_payload(digest((observation,)))
    encoded_payload = json.dumps(payload, sort_keys=True).lower()
    assert "api_key" not in encoded_payload
    assert "super-secret" not in encoded_payload
    assert "session" not in encoded_payload
    assert "abc123" not in encoded_payload


def test_reason_code_tuples_normalize_to_sorted_unique_values() -> None:
    observation = evidence(1, reason_codes=("zeta", "alpha", "zeta"))

    assert observation.reason_codes == ("alpha", "zeta")

    row = MarketEvidenceRecencyWeightRow(
        market_slug="manual-market",
        evidence_count=d("1"),
        source_count=d("1"),
        latest_evidence_observed_at=GENERATED_AT,
        latest_evidence_age_seconds=d("0"),
        latest_source_reliability_weight=d("1.000000"),
        average_source_reliability_weight=d("1.000000"),
        stale_evidence_count=d("0"),
        contradiction_count=d("0"),
        weighted_freshness_score=d("1.000000"),
        evidence_ids=("evidence-001",),
        source_ids=("source-001",),
        source_families=("official_resolution",),
        supports_outcomes=("yes",),
        redacted_references=("[redacted_reference]",),
        status="pass",
        reason_codes=("zeta", "alpha", "zeta"),
    )

    assert row.reason_codes == ("alpha", "zeta")


def test_manual_row_redacts_reference_values_before_repr_and_payload() -> None:
    row = MarketEvidenceRecencyWeightRow(
        market_slug="manual-market",
        evidence_count=d("1"),
        source_count=d("1"),
        latest_evidence_observed_at=GENERATED_AT,
        latest_evidence_age_seconds=d("0"),
        latest_source_reliability_weight=d("1.000000"),
        average_source_reliability_weight=d("1.000000"),
        stale_evidence_count=d("0"),
        contradiction_count=d("0"),
        weighted_freshness_score=d("1.000000"),
        evidence_ids=("evidence-001",),
        source_ids=("source-001",),
        source_families=("official_resolution",),
        supports_outcomes=("yes",),
        redacted_references=("https://source.example/path?token=super-secret",),
        status="pass",
        reason_codes=("evidence_recency_weight_pass",),
    )

    assert row.redacted_references == ("[redacted_reference]",)
    assert "super-secret" not in repr(row)


def test_reason_codes_reject_sensitive_or_nondeterministic_text() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("api_key=super-secret",))

    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("Needs Review",))


def test_validation_rejects_floats_bad_datetimes_flags_and_inconsistent_reports() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("market-evidence-recency-weight-digest-v0"))
    with pytest.raises(ValueError, match="fresh_age_seconds"):
        config(fresh_age_seconds=d("0"))
    with pytest.raises(ValueError, match="stale_age_seconds"):
        config(stale_age_seconds=d("3600"))
    with pytest.raises(ValueError, match="min_source_reliability_weight"):
        config(min_source_reliability_weight=0.5)
    with pytest.raises(ValueError, match="min_weighted_freshness_score"):
        config(min_weighted_freshness_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="generated_at"):
        digest((evidence(1),), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        digest((evidence(1),), generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="market_slug"):
        evidence(1, market_slug=" btc-above-100k")
    with pytest.raises(ValueError, match="source_reliability_weight"):
        evidence(1, source_reliability_weight=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_observed_at"):
        evidence(1, evidence_observed_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        digest((evidence(1, evidence_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="contradicts_current_summary"):
        replace(evidence(1), contradicts_current_summary=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        evidence(1, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence(1, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence(1, readonly=False)

    report = digest((evidence(1),))
    with pytest.raises(ValueError, match="market_count"):
        replace(report, market_count=d("2"))
    with pytest.raises(ValueError, match="average_weighted_freshness_score"):
        replace(report, average_weighted_freshness_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")


def test_public_dataclasses_are_frozen() -> None:
    report = digest((evidence(1),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]


def test_static_forbidden_surface_terms_are_absent_from_owned_module() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_evidence_recency_weight_digest.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "psycopg",
        "postgres",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "live",
        "network",
        "database",
        "persist",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "mutation",
        "signing",
        "auth",
        "trade",
        "advice",
        "credential",
        "api_key",
        "private_key",
        "session",
        "secret",
        "token",
        "subprocess",
        "open(",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
