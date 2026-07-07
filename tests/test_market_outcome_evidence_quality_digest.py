from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_outcome_evidence_quality_digest import (
    MarketOutcomeEvidenceObservation,
    MarketOutcomeEvidenceQualityConfig,
    MarketOutcomeEvidenceQualityDigest,
    MarketOutcomeEvidenceQualityRow,
    build_market_outcome_evidence_quality_digest,
    market_outcome_evidence_quality_digest_to_json_payload,
    validate_market_outcome_evidence_quality_digest_public_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketOutcomeEvidenceQualityConfig:
    values = {
        "config_version": "market-outcome-evidence-quality-digest-v0",
        "max_evidence_age_seconds": d("86400"),
        "max_acknowledgement_age_seconds": d("43200"),
        "authoritative_source_kinds": ("resolution_source", "official_notice"),
        "min_source_agreement_ratio": d("1.000000"),
        "max_unresolved_ambiguity_ratio": d("0.000000"),
    }
    values.update(overrides)
    return MarketOutcomeEvidenceQualityConfig(**values)


def observation(index: int, **overrides: object) -> MarketOutcomeEvidenceObservation:
    values = {
        "market_slug": "btc-above-100k",
        "category_id": "finance.crypto.btc",
        "evidence_id": f"evidence-{index:03d}",
        "source_id": f"source-{index:03d}",
        "source_kind": "resolution_source",
        "observed_outcome": "yes",
        "evidence_observed_at": GENERATED_AT - timedelta(hours=1),
        "acknowledged_at": GENERATED_AT - timedelta(minutes=30),
        "unresolved_ambiguity": False,
        "reason_codes": (),
    }
    values.update(overrides)
    return MarketOutcomeEvidenceObservation(**values)


def digest(
    evidence: tuple[MarketOutcomeEvidenceObservation, ...] | list[MarketOutcomeEvidenceObservation],
    *,
    cfg: MarketOutcomeEvidenceQualityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketOutcomeEvidenceQualityDigest:
    return build_market_outcome_evidence_quality_digest(
        evidence,
        config=cfg or config(),
        generated_at=generated_at,
    )


def payload_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def test_empty_input_returns_report_only_zero_digest() -> None:
    report = digest(())

    assert type(report) is MarketOutcomeEvidenceQualityDigest
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-outcome-evidence-quality-digest-v0"
    assert report.market_count == d("0")
    assert report.category_count == d("0")
    assert report.evidence_count == d("0")
    assert report.high_quality_market_count == d("0")
    assert report.rows == ()
    assert report.category_rollups == ()
    assert report.reason_code_counts == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_quality_evidence_emits_market_and_category_rollup() -> None:
    report = digest(
        (
            observation(1, source_id="official", source_kind="resolution_source"),
            observation(2, source_id="secondary", source_kind="news_archive"),
        ),
    )

    assert report.market_count == d("1")
    assert report.category_count == d("1")
    assert report.evidence_count == d("2")
    assert report.high_quality_market_count == d("1")
    row = report.rows[0]
    assert type(row) is MarketOutcomeEvidenceQualityRow
    assert row.market_slug == "btc-above-100k"
    assert row.category_id == "finance.crypto.btc"
    assert row.evidence_count == d("2")
    assert row.authoritative_source_count == d("1")
    assert row.authoritative_source_present is True
    assert row.source_agreement_ratio == d("1.000000")
    assert row.latest_evidence_age_seconds == d("3600")
    assert row.evidence_fresh is True
    assert row.latest_acknowledgement_age_seconds == d("1800")
    assert row.acknowledgement_fresh is True
    assert row.unresolved_ambiguity_count == d("0")
    assert row.unresolved_ambiguity_ratio == d("0.000000")
    assert row.quality_status == "high_quality"
    assert row.reason_codes == (
        "acknowledgement_fresh",
        "ambiguity_clear",
        "evidence_fresh",
        "has_authoritative_source",
        "high_quality_evidence",
        "sources_agree",
    )

    category = report.category_rollups[0]
    assert category.category_id == "finance.crypto.btc"
    assert category.market_count == d("1")
    assert category.evidence_count == d("2")
    assert category.high_quality_market_count == d("1")
    assert category.high_quality_market_ratio == d("1.000000")
    assert category.reason_code_counts[0].reason_code == "acknowledgement_fresh"
    assert category.reason_code_counts[0].market_count == d("1")
    assert category.reason_code_counts[0].market_ratio == d("1.000000")


def test_stale_evidence_marks_age_and_reason_code() -> None:
    report = digest(
        (
            observation(
                1,
                evidence_observed_at=GENERATED_AT - timedelta(days=3),
            ),
        ),
    )

    row = report.rows[0]
    assert row.latest_evidence_age_seconds == d("259200")
    assert row.evidence_fresh is False
    assert row.quality_status == "stale_evidence"
    assert "evidence_stale" in row.reason_codes
    assert report.stale_evidence_market_count == d("1")


def test_source_disagreement_reduces_agreement_ratio() -> None:
    report = digest(
        (
            observation(1, observed_outcome="yes"),
            observation(2, observed_outcome="no", source_kind="news_archive"),
            observation(3, observed_outcome="yes", source_kind="news_archive"),
        ),
    )

    row = report.rows[0]
    assert row.unique_outcome_count == d("2")
    assert row.source_agreement_ratio == d("0.666667")
    assert row.source_agreement_present is False
    assert row.quality_status == "source_disagreement"
    assert "sources_disagree" in row.reason_codes
    assert report.source_disagreement_market_count == d("1")


def test_missing_authoritative_source_is_reported() -> None:
    report = digest(
        (
            observation(1, source_kind="community_thread"),
            observation(2, source_kind="news_archive"),
        ),
    )

    row = report.rows[0]
    assert row.authoritative_source_count == d("0")
    assert row.authoritative_source_present is False
    assert row.quality_status == "missing_authoritative_source"
    assert "missing_authoritative_source" in row.reason_codes
    assert report.missing_authoritative_source_market_count == d("1")


def test_unresolved_ambiguity_pressure_is_reported() -> None:
    report = digest(
        (
            observation(1, unresolved_ambiguity=True, reason_codes=("ambiguous_wording",)),
            observation(2, source_kind="news_archive"),
        ),
    )

    row = report.rows[0]
    assert row.unresolved_ambiguity_count == d("1")
    assert row.unresolved_ambiguity_ratio == d("0.500000")
    assert row.quality_status == "unresolved_ambiguity"
    assert "unresolved_ambiguity" in row.reason_codes
    assert "input_ambiguous_wording" in row.reason_codes
    assert report.unresolved_ambiguity_market_count == d("1")


def test_rows_categories_and_reason_codes_sort_deterministically() -> None:
    report = digest(
        (
            observation(
                1,
                market_slug="z-market",
                category_id="sports.soccer",
                evidence_id="z-2",
                reason_codes=("zeta", "alpha"),
            ),
            observation(
                2,
                market_slug="a-market",
                category_id="finance.crypto.btc",
                evidence_id="a-1",
                reason_codes=("alpha",),
            ),
            observation(
                3,
                market_slug="z-market",
                category_id="sports.soccer",
                evidence_id="z-1",
                source_kind="news_archive",
                reason_codes=("alpha",),
            ),
        ),
    )

    assert [(row.category_id, row.market_slug) for row in report.rows] == [
        ("finance.crypto.btc", "a-market"),
        ("sports.soccer", "z-market"),
    ]
    assert [category.category_id for category in report.category_rollups] == [
        "finance.crypto.btc",
        "sports.soccer",
    ]
    z_row = report.rows[1]
    assert z_row.evidence_ids == ("z-1", "z-2")
    assert z_row.reason_codes == (
        "acknowledgement_fresh",
        "ambiguity_clear",
        "evidence_fresh",
        "has_authoritative_source",
        "high_quality_evidence",
        "input_alpha",
        "input_zeta",
        "sources_agree",
    )
    assert [item.reason_code for item in report.reason_code_counts] == sorted(
        item.reason_code for item in report.reason_code_counts
    )


def test_json_payload_uses_decimal_strings_and_no_public_numbers() -> None:
    payload = market_outcome_evidence_quality_digest_to_json_payload(
        digest((observation(1),)),
    )

    assert payload["market_count"] == "1"
    assert payload["rows"][0]["source_agreement_ratio"] == "1.000000"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert validate_market_outcome_evidence_quality_digest_public_payload(payload) is True

    def walk(value: object) -> None:
        assert not isinstance(value, float)
        assert type(value) is not int
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)


def test_derived_validation_digest_is_payload_bound_and_tamper_evident() -> None:
    report = digest((observation(1),))
    payload = market_outcome_evidence_quality_digest_to_json_payload(report)

    assert report.derived_validation_digest == payload["derived_validation_digest"]
    assert all(
        character in "0123456789abcdef"
        for character in report.derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["market_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_market_outcome_evidence_quality_digest_public_payload(tampered_payload)

    tampered_report = digest((observation(1),))
    object.__setattr__(
        tampered_report.rows[0],
        "source_agreement_ratio",
        d("0.500000"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_outcome_evidence_quality_digest_to_json_payload(tampered_report)


def test_manual_digest_rejects_inconsistent_rollups_and_reason_counts() -> None:
    report = digest((observation(1),))
    inconsistent_rollup = replace(
        report.category_rollups[0],
        high_quality_market_count=d("0"),
    )

    with pytest.raises(ValueError, match="category_rollups"):
        replace(
            report,
            category_rollups=(inconsistent_rollup,),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=(), derived_validation_digest="")


def test_public_payload_requires_nested_report_only_flags() -> None:
    payload = market_outcome_evidence_quality_digest_to_json_payload(
        digest((observation(1),)),
    )
    payload["rows"][0]["readonly"] = False
    payload["derived_validation_digest"] = payload_digest(payload)

    with pytest.raises(ValueError, match="readonly"):
        validate_market_outcome_evidence_quality_digest_public_payload(payload)


def test_public_payload_rejects_missing_nested_hard_flag() -> None:
    payload = market_outcome_evidence_quality_digest_to_json_payload(
        digest((observation(1),)),
    )
    del payload["rows"][0]["readonly"]
    payload["derived_validation_digest"] = payload_digest(payload)

    with pytest.raises(ValueError, match="readonly"):
        validate_market_outcome_evidence_quality_digest_public_payload(payload)


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "token=abc123",
        "password=hunter2",
        "bearer abc123",
    ),
)
def test_payload_rejects_sensitive_public_strings(unsafe_text: str) -> None:
    with pytest.raises(ValueError, match="sensitive"):
        market_outcome_evidence_quality_digest_to_json_payload(
            digest((observation(1, source_id=unsafe_text),)),
        )


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "live trading enabled",
        "authorization header",
        "wallet address",
        "place_order endpoint",
        "network client",
        "database write",
        "persist to disk",
    ),
)
def test_public_payload_rejects_unsafe_surface_terms(unsafe_text: str) -> None:
    payload = market_outcome_evidence_quality_digest_to_json_payload(
        digest((observation(1),)),
    )
    payload[unsafe_text] = "blocked"

    with pytest.raises(ValueError, match="unsafe|sensitive"):
        validate_market_outcome_evidence_quality_digest_public_payload(payload)


@pytest.mark.parametrize(
    ("factory", "match"),
    (
        (lambda: config(config_version=""), "config_version"),
        (lambda: config(config_version=_StringSubclass("v0")), "config_version"),
        (lambda: config(max_evidence_age_seconds=d("-1")), "max_evidence_age_seconds"),
        (
            lambda: config(max_evidence_age_seconds=_DecimalSubclass("1")),
            "max_evidence_age_seconds",
        ),
        (lambda: config(min_source_agreement_ratio=d("1.0000001")), "min_source_agreement_ratio"),
        (lambda: config(authoritative_source_kinds=("resolution_source", "")), "authoritative_source_kinds"),
        (lambda: observation(1, market_slug=""), "market_slug"),
        (lambda: observation(1, source_kind=_StringSubclass("resolution_source")), "source_kind"),
        (lambda: observation(1, evidence_observed_at="2026-07-02"), "evidence_observed_at"),
        (
            lambda: observation(
                1,
                evidence_observed_at=datetime(2026, 7, 2, 12, 0),
            ),
            "evidence_observed_at",
        ),
        (
            lambda: observation(
                1,
                acknowledged_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
            ),
            "acknowledged_at",
        ),
        (
            lambda: digest((), generated_at=datetime(2026, 7, 2, 12, 0)),
            "generated_at",
        ),
        (
            lambda: digest((), generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC)),
            "generated_at",
        ),
        (lambda: digest((observation(1),), cfg=object()), "config"),
        (lambda: digest((object(),)), "evidence"),
        (lambda: digest((observation(1, paper_only=False),)), "paper_only"),
        (lambda: config(readonly=False), "readonly"),
    ),
)
def test_validation_errors(factory: object, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        factory()


def test_dataclasses_are_frozen_and_flags_are_hard() -> None:
    report = digest((observation(1),))

    with pytest.raises(FrozenInstanceError):
        report.market_count = d("2")
    with pytest.raises(FrozenInstanceError):
        report.rows[0].quality_status = "changed"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.category_rollups[0], readonly=False)


def test_public_dataclasses_reject_subclassing() -> None:
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(MarketOutcomeEvidenceQualityConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(MarketOutcomeEvidenceObservation):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeDigest(MarketOutcomeEvidenceQualityDigest):
            pass


def test_payload_revalidates_tampered_public_numeric_and_flag_values() -> None:
    numeric_tampered = digest((observation(1),))
    object.__setattr__(numeric_tampered, "market_count", 1)
    with pytest.raises(ValueError, match="market_count|Decimal"):
        market_outcome_evidence_quality_digest_to_json_payload(numeric_tampered)

    flag_tampered = digest((observation(1),))
    object.__setattr__(flag_tampered.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_outcome_evidence_quality_digest_to_json_payload(flag_tampered)


def test_static_forbidden_surface_terms_are_absent() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_outcome_evidence_quality_digest",
    )
    source = Path(module.__file__).read_text(encoding="utf-8")
    forbidden_terms = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "wallet",
        "broker",
        "place_order",
        "sign_transaction",
        "private_key",
        "api_key",
        "secret_key",
        "live_trading",
        "financial_advice",
        "network",
        "database",
        "persist",
        "total_seconds(",
        "open(",
    )

    for term in forbidden_terms:
        assert term not in source
