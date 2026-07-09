from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_authority_scrapling_consensus_decay_report import (
    ResearchSourceAuthorityScraplingConsensusDecayConfig,
    ResearchSourceAuthorityScraplingConsensusDecayObservation,
    ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount,
    ResearchSourceAuthorityScraplingConsensusDecayReport,
    ResearchSourceAuthorityScraplingConsensusDecayRow,
    build_research_source_authority_scrapling_consensus_decay_report,
    research_source_authority_scrapling_consensus_decay_report_payload,
    validate_research_source_authority_scrapling_consensus_decay_public_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchSourceAuthorityScraplingConsensusDecayConfig:
    values = {
        "config_version": "research-source-authority-scrapling-consensus-decay-v0",
        "fresh_age_seconds": d("3600"),
        "stale_age_seconds": d("86400"),
        "min_consensus_source_family_count": d("2"),
        "pass_score_threshold": d("0.700000"),
        "watch_score_threshold": d("0.400000"),
        "authority_weight": d("0.450000"),
        "consensus_weight": d("0.350000"),
        "recency_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchSourceAuthorityScraplingConsensusDecayConfig(**values)


def observation(
    index: int,
    *,
    candidate_reference: str = "raw-candidate-alpha",
    source_reference: str | None = None,
    source_family: str = "official",
    authority_score: Decimal | None = None,
    observed_at: datetime | None = None,
) -> ResearchSourceAuthorityScraplingConsensusDecayObservation:
    return ResearchSourceAuthorityScraplingConsensusDecayObservation(
        candidate_reference=candidate_reference,
        source_reference=source_reference or f"source-{index:03d}",
        source_family=source_family,
        authority_score=authority_score or d("0.900000"),
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=15)
        ),
    )


def report(
    rows: tuple[ResearchSourceAuthorityScraplingConsensusDecayObservation, ...],
    *,
    cfg: ResearchSourceAuthorityScraplingConsensusDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceAuthorityScraplingConsensusDecayReport:
    return build_research_source_authority_scrapling_consensus_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_without_rows() -> None:
    authority_report = report(())

    assert type(authority_report) is ResearchSourceAuthorityScraplingConsensusDecayReport
    assert authority_report.status == "block"
    assert authority_report.candidate_count == d("0.000000")
    assert authority_report.observation_count == d("0.000000")
    assert authority_report.pass_count == d("0.000000")
    assert authority_report.watch_count == d("0.000000")
    assert authority_report.block_count == d("0.000000")
    assert authority_report.average_scrapling_consensus_decay_score is None
    assert authority_report.reason_codes == ("no_scrapling_consensus_observations",)
    assert authority_report.reason_code_counts == (
        ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount(
            reason_code="no_scrapling_consensus_observations",
            count=d("1.000000"),
        ),
    )
    assert authority_report.rows == ()
    assert authority_report.paper_only is True
    assert authority_report.report_only is True
    assert authority_report.readonly is True


def test_diverse_authoritative_fresh_sources_pass_with_redacted_public_payload() -> None:
    authority_report = report(
        (
            observation(
                2,
                candidate_reference="raw-candidate-alpha",
                source_reference="venue-source",
                source_family="venue",
                authority_score=d("0.800000"),
                observed_at=GENERATED_AT - timedelta(minutes=20),
            ),
            observation(
                1,
                candidate_reference="raw-candidate-alpha",
                source_reference="official-source",
                source_family="official",
                authority_score=d("0.900000"),
                observed_at=GENERATED_AT - timedelta(minutes=15),
            ),
        ),
    )

    row = authority_report.rows[0]
    assert type(row) is ResearchSourceAuthorityScraplingConsensusDecayRow
    assert authority_report.status == "pass"
    assert authority_report.candidate_count == d("1.000000")
    assert authority_report.observation_count == d("2.000000")
    assert authority_report.pass_count == d("1.000000")
    assert authority_report.watch_count == d("0.000000")
    assert authority_report.block_count == d("0.000000")
    assert authority_report.average_scrapling_consensus_decay_score == d("0.932500")
    assert row.candidate_digest.startswith("sha256:")
    assert row.evidence_count == d("2.000000")
    assert row.source_count == d("2.000000")
    assert row.source_family_count == d("2.000000")
    assert row.latest_observed_at == GENERATED_AT - timedelta(minutes=15)
    assert row.latest_source_age_seconds == d("900.000000")
    assert row.average_authority_score == d("0.850000")
    assert row.consensus_score == d("1.000000")
    assert row.recency_score == d("1.000000")
    assert row.scrapling_consensus_decay_score == d("0.932500")
    assert row.status == "pass"
    assert row.reason_codes == ("scrapling_consensus_decay_pass",)

    payload = research_source_authority_scrapling_consensus_decay_report_payload(
        authority_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["derived_validation_digest"] == authority_report.derived_validation_digest
    assert payload["rows"][0]["candidate_digest"] == row.candidate_digest
    assert "raw-candidate-alpha" not in encoded
    assert "official-source" not in encoded
    assert "venue-source" not in encoded
    assert "market_id" not in encoded
    assert "market_slug" not in encoded
    assert "question" not in encoded
    assert "source_url" not in encoded
    assert "source_text" not in encoded
    assert "dsn" not in encoded
    assert "table_name" not in encoded
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))
    validate_research_source_authority_scrapling_consensus_decay_public_payload(payload)


def test_weak_consensus_watches_and_stale_low_authority_blocks() -> None:
    authority_report = report(
        (
            observation(
                1,
                candidate_reference="raw-candidate-watch",
                source_reference="official-watch",
                source_family="official",
                authority_score=d("0.900000"),
            ),
            observation(
                2,
                candidate_reference="raw-candidate-block",
                source_reference="official-block",
                source_family="official",
                authority_score=d("0.300000"),
                observed_at=GENERATED_AT - timedelta(days=2),
            ),
        ),
    )

    assert authority_report.status == "block"
    assert tuple(row.status for row in authority_report.rows) == ("block", "watch")
    blocked, watched = authority_report.rows
    assert blocked.reason_codes == (
        "source_authority_below_watch_threshold",
        "scrapling_consensus_observations_stale",
        "scrapling_consensus_decay_below_watch_threshold",
        "scrapling_consensus_decay_block",
    )
    assert watched.reason_codes == (
        "insufficient_independent_consensus",
        "scrapling_consensus_decay_watch",
    )
    assert authority_report.reason_codes == (
        "source_authority_below_watch_threshold",
        "insufficient_independent_consensus",
        "scrapling_consensus_observations_stale",
        "scrapling_consensus_decay_below_watch_threshold",
        "scrapling_consensus_decay_block",
        "scrapling_consensus_decay_watch",
    )


def test_payload_digest_and_surface_validation_reject_tampering() -> None:
    payload = research_source_authority_scrapling_consensus_decay_report_payload(
        report((observation(1), observation(2, source_family="analysis"))),
    )

    tampered_status = dict(payload)
    tampered_status["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_source_authority_scrapling_consensus_decay_public_payload(
            tampered_status,
        )

    tampered_numeric = dict(payload)
    tampered_numeric["candidate_count"] = 1
    with pytest.raises(ValueError, match="Decimal-derived strings"):
        validate_research_source_authority_scrapling_consensus_decay_public_payload(
            tampered_numeric,
        )

    tampered_surface = dict(payload)
    tampered_surface["rows"] = [dict(payload["rows"][0], market_id="market-123")]
    with pytest.raises(ValueError, match="unsafe"):
        validate_research_source_authority_scrapling_consensus_decay_public_payload(
            tampered_surface,
        )


def test_validation_rejects_bad_types_future_times_bad_flags_and_unsafe_inputs() -> None:
    with pytest.raises(ValueError, match="authority_weight"):
        config(authority_weight=d("0.500000"))
    with pytest.raises(ValueError, match="pass_score_threshold"):
        config(pass_score_threshold=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="recency_weight"):
        config(recency_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(1),),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="candidate_reference"):
        observation(1, candidate_reference=" https://example.test/market ")
    with pytest.raises(ValueError, match="source_reference"):
        observation(1, source_reference="https://example.test/source")
    with pytest.raises(ValueError, match="source_family"):
        observation(1, source_family="official source")
    with pytest.raises(ValueError, match="authority_score"):
        observation(1, authority_score=d("1.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    authority_report = report((observation(1), observation(2, source_family="analysis")))

    with pytest.raises(FrozenInstanceError):
        authority_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        authority_report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(authority_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="candidate_count"):
        replace(authority_report, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(authority_report, derived_validation_digest="0" * 64)


def test_owned_module_has_no_db_network_filesystem_execution_or_live_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_authority_scrapling_consensus_decay_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "psycopg",
        "sqlalchemy",
        "web3",
        "clob",
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
