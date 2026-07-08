from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_confidence_decay_report import (
    ResearchSourceConfidenceDecayConfig,
    ResearchSourceConfidenceDecayEvidence,
    ResearchSourceConfidenceDecayReport,
    build_research_source_confidence_decay_report,
    research_source_confidence_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceConfidenceDecayConfig:
    values = {
        "config_version": "research-source-confidence-decay-report-v0",
        "fresh_age_seconds": d("3600"),
        "stale_age_seconds": d("86400"),
        "pass_decayed_confidence_score": d("0.700000"),
        "block_decayed_confidence_score": d("0.250000"),
    }
    values.update(overrides)
    return ResearchSourceConfidenceDecayConfig(**values)


def evidence(
    index: int,
    *,
    source_class: str = "official",
    source_confidence: Decimal = d("0.900000"),
    observed_at: datetime | None = None,
    source_locator: str | None = None,
    evidence_excerpt: str | None = None,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceConfidenceDecayEvidence:
    return ResearchSourceConfidenceDecayEvidence(
        evidence_key=f"candidate-{index:03d}",
        source_class=source_class,
        source_confidence=source_confidence,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        source_locator=(
            source_locator
            if source_locator is not None
            else f"https://source.example/{index}?token=super-secret"
        ),
        evidence_excerpt=(
            evidence_excerpt
            if evidence_excerpt is not None
            else f"Raw market question text {index} with private details"
        ),
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceConfidenceDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceConfidenceDecayReport:
    return build_research_source_confidence_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_with_report_only_zero_counts() -> None:
    result = report(())
    payload = research_source_confidence_decay_report_payload(result)

    assert result.status == "block"
    assert result.evidence_count == d("0")
    assert result.bucket_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.average_decayed_confidence_score is None
    assert result.rows == ()
    assert result.reason_codes == ("no_source_confidence_evidence",)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_aggregates_source_confidence_decay_by_class_and_age_bucket() -> None:
    result = report(
        (
            evidence(2, observed_at=GENERATED_AT - timedelta(hours=12), source_confidence=d("0.800000")),
            evidence(1, observed_at=GENERATED_AT - timedelta(minutes=30), source_confidence=d("0.900000")),
            evidence(
                3,
                source_class="social",
                observed_at=GENERATED_AT - timedelta(days=2),
                source_confidence=d("0.900000"),
                reason_codes=("low_verification_depth",),
            ),
        ),
    )

    assert result.status == "block"
    assert result.evidence_count == d("3")
    assert result.bucket_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.average_decayed_confidence_score == d("0.433333")
    assert tuple((row.source_class, row.age_bucket, row.status) for row in result.rows) == (
        ("official", "aging", "watch"),
        ("official", "fresh", "pass"),
        ("social", "stale", "block"),
    )
    assert result.rows[0].average_age_seconds == d("43200")
    assert result.rows[0].average_age_decay_factor == d("0.500000")
    assert result.rows[0].average_decayed_confidence_score == d("0.400000")
    assert result.rows[1].average_age_decay_factor == d("1.000000")
    assert result.rows[2].average_age_decay_factor == d("0.000000")
    assert "input_low_verification_depth" in result.rows[2].reason_codes


def test_public_payload_redacts_raw_ids_locators_and_excerpt_text() -> None:
    observation = evidence(
        7,
        source_locator="https://private-source.example/path?api_key=super-secret&session=abc123",
        evidence_excerpt="Will candidate-alpha market question resolve yes?",
    )
    result = report((observation,))
    payload = research_source_confidence_decay_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert observation.source_locator == "[redacted_source_locator]"
    assert observation.evidence_excerpt == "[redacted_evidence_excerpt]"
    assert "candidate-007" not in encoded
    assert "candidate-alpha" not in encoded
    assert "market question" not in encoded
    assert "https://" not in encoded
    assert "private-source" not in encoded
    assert "api_key" not in encoded
    assert "super-secret" not in encoded
    assert "session" not in encoded
    assert "abc123" not in encoded
    assert "source_locator" not in encoded
    assert "evidence_excerpt" not in encoded


def test_payload_uses_decimal_strings_and_validates_digest() -> None:
    result = report((evidence(1), evidence(2, source_class="analyst")))
    payload = research_source_confidence_decay_report_payload(result)

    assert research_source_confidence_decay_report_payload(payload) == payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["evidence_count"] == "2"
    assert payload["rows"][0]["average_decayed_confidence_score"] == "0.900000"
    assert type(result.derived_validation_digest) is str
    assert len(result.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in result.derived_validation_digest)
    assert all(len(row.derived_validation_digest) == 64 for row in result.rows)
    assert not any(type(value) in (Decimal, int, float) for value in _walk_payload_values(payload))

    numeric_payload = json.loads(json.dumps(payload))
    numeric_payload["evidence_count"] = 2
    with pytest.raises(ValueError, match="evidence_count"):
        research_source_confidence_decay_report_payload(numeric_payload)

    tampered_payload = json.loads(json.dumps(payload))
    tampered_payload["bucket_count"] = "3"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_confidence_decay_report_payload(tampered_payload)

    missing_digest_payload = json.loads(json.dumps(payload))
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_confidence_decay_report_payload(missing_digest_payload)


def test_validation_rejects_floats_bad_datetimes_flags_and_unsafe_payloads() -> None:
    with pytest.raises(ValueError, match="fresh_age_seconds"):
        config(fresh_age_seconds=d("0"))
    with pytest.raises(ValueError, match="stale_age_seconds"):
        config(stale_age_seconds=d("3600"))
    with pytest.raises(ValueError, match="pass_decayed_confidence_score"):
        config(pass_decayed_confidence_score=0.7)
    with pytest.raises(ValueError, match="block_decayed_confidence_score"):
        config(block_decayed_confidence_score=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_confidence"):
        evidence(1, source_confidence=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        evidence(1, observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((evidence(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        evidence(1, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence(1, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence(1, readonly=False)

    payload = research_source_confidence_decay_report_payload(report((evidence(1),)))
    unsafe_payload = json.loads(json.dumps(payload))
    unsafe_payload["market_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe"):
        research_source_confidence_decay_report_payload(unsafe_payload)


def test_public_dataclasses_are_frozen_and_module_has_no_forbidden_surfaces() -> None:
    result = report((evidence(1),))

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "watch"  # type: ignore[misc]

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_confidence_decay_report.py"
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
        "candidate_id",
        "market_id",
        "source_url",
        "source_text",
        "dsn",
        "table",
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
