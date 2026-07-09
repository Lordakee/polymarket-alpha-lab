from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_claim_resolution_authority_lag_report import (
    ResearchEventClaimResolutionAuthorityLagCandidate,
    ResearchEventClaimResolutionAuthorityLagConfig,
    ResearchEventClaimResolutionAuthorityLagReport,
    build_research_event_claim_resolution_authority_lag_report,
    research_event_claim_resolution_authority_lag_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
RESOLUTION_AT = GENERATED_AT - timedelta(hours=80)
OBSERVED_AT = GENERATED_AT - timedelta(hours=1)


def candidate(
    candidate_id: str = "candidate-raw-001",
    market_id: str = "market-raw-001",
    market_slug: str = "will-raw-candidate-win-2026",
    market_question: str = "Will Raw Candidate win the 2026 certified event?",
    resolution_authority_id: str = "official-authority-raw-001",
    claim_category: str = "election",
    *,
    resolution_at: datetime = RESOLUTION_AT,
    authority_reported_at: datetime | None = RESOLUTION_AT + timedelta(hours=6),
    observed_at: datetime = OBSERVED_AT,
    resolver_confirmation_count: Decimal = Decimal("2"),
    conflicting_resolver_count: Decimal = Decimal("0"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchEventClaimResolutionAuthorityLagCandidate:
    return ResearchEventClaimResolutionAuthorityLagCandidate(
        candidate_id=candidate_id,
        market_id=market_id,
        market_slug=market_slug,
        market_question=market_question,
        resolution_authority_id=resolution_authority_id,
        claim_category=claim_category,
        resolution_at=resolution_at,
        authority_reported_at=authority_reported_at,
        observed_at=observed_at,
        resolver_confirmation_count=resolver_confirmation_count,
        conflicting_resolver_count=conflicting_resolver_count,
        reason_codes=reason_codes,
    )


def test_empty_input_returns_report_only_pass_digest() -> None:
    report = build_research_event_claim_resolution_authority_lag_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchEventClaimResolutionAuthorityLagConfig(),
    )

    assert report == ResearchEventClaimResolutionAuthorityLagReport(
        generated_at=GENERATED_AT,
        config_version="research_event_claim_resolution_authority_lag_report",
        row_count=Decimal("0"),
        pass_count=Decimal("0"),
        watch_count=Decimal("0"),
        block_count=Decimal("0"),
        average_authority_lag_hours=Decimal("0"),
        maximum_authority_lag_hours=Decimal("0"),
        status="pass",
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_rows_statuses_counts_and_public_payload_redaction() -> None:
    config = ResearchEventClaimResolutionAuthorityLagConfig()
    inputs = (
        candidate(
            candidate_id="candidate-pass-raw",
            market_id="market-pass-raw",
            market_slug="raw-pass-market-slug",
            market_question="Will the pass candidate resolve?",
            authority_reported_at=RESOLUTION_AT + timedelta(hours=6),
            reason_codes=("manual_reviewed",),
        ),
        candidate(
            candidate_id="candidate-watch-raw",
            market_id="market-watch-raw",
            market_slug="raw-watch-market-slug",
            market_question="Will the watch candidate resolve?",
            authority_reported_at=RESOLUTION_AT + timedelta(hours=30),
            reason_codes=("manual_reviewed",),
        ),
        candidate(
            candidate_id="candidate-block-raw",
            market_id="market-block-raw",
            market_slug="raw-block-market-slug",
            market_question="Will the block candidate resolve?",
            authority_reported_at=None,
        ),
    )

    report = build_research_event_claim_resolution_authority_lag_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )
    payload = research_event_claim_resolution_authority_lag_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert [row.lag_status for row in report.rows] == sorted(
        row.lag_status for row in report.rows
    )
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")
    assert report.status == "block"
    assert report.average_authority_lag_hours == Decimal("18.0000")
    assert report.maximum_authority_lag_hours == Decimal("30.0000")

    pass_row = next(row for row in report.rows if row.lag_status == "pass")
    watch_row = next(row for row in report.rows if row.lag_status == "watch")
    block_row = next(row for row in report.rows if row.lag_status == "block")

    assert pass_row.authority_lag_hours == Decimal("6.0000")
    assert pass_row.reason_codes == ("authority_lag_pass", "manual_reviewed")
    assert watch_row.authority_lag_hours == Decimal("30.0000")
    assert "authority_lag_watch" in watch_row.reason_codes
    assert block_row.authority_lag_hours is None
    assert "missing_authority_report" in block_row.reason_codes
    assert all(row.claim_fingerprint.startswith("sha256:") for row in report.rows)
    assert all(row.resolver_fingerprint.startswith("sha256:") for row in report.rows)
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)

    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["row_count"] == "3.0000"
    assert payload["average_authority_lag_hours"] == "18.0000"
    assert payload["rows"][0]["lag_status"] in ("pass", "watch", "block")
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))

    for leaked in (
        "candidate-pass-raw",
        "candidate-watch-raw",
        "candidate-block-raw",
        "market-pass-raw",
        "market-watch-raw",
        "market-block-raw",
        "raw-pass-market-slug",
        "raw-watch-market-slug",
        "raw-block-market-slug",
        "Will the pass candidate resolve?",
        "Will the watch candidate resolve?",
        "Will the block candidate resolve?",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
    ):
        assert leaked not in encoded


def test_rows_reason_counts_and_digest_are_deterministic() -> None:
    config = ResearchEventClaimResolutionAuthorityLagConfig()
    inputs = (
        candidate(
            "candidate-z",
            "market-z",
            "slug-z",
            "Question Z?",
            authority_reported_at=RESOLUTION_AT + timedelta(hours=30),
            reason_codes=("zeta", "alpha"),
        ),
        candidate(
            "candidate-a",
            "market-a",
            "slug-a",
            "Question A?",
            authority_reported_at=RESOLUTION_AT + timedelta(hours=6),
            reason_codes=("alpha",),
        ),
    )

    report = build_research_event_claim_resolution_authority_lag_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_research_event_claim_resolution_authority_lag_report(
        tuple(reversed(inputs)),
        generated_at=GENERATED_AT,
        config=config,
    )
    payload = research_event_claim_resolution_authority_lag_report_payload(report)

    assert reversed_report.rows == report.rows
    assert reversed_report.derived_validation_digest == report.derived_validation_digest
    assert report.reason_code_counts == (
        ("alpha", Decimal("2")),
        ("authority_lag_pass", Decimal("1")),
        ("authority_lag_watch", Decimal("1")),
        ("zeta", Decimal("1")),
    )
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "4.0000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_claim_resolution_authority_lag_report_payload(tampered_payload)

    unsafe_payload = dict(payload)
    unsafe_payload["candidate_id"] = "candidate-raw"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_claim_resolution_authority_lag_report_payload(unsafe_payload)

    unsafe_payload = dict(payload)
    unsafe_payload["wallet_ref"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_claim_resolution_authority_lag_report_payload(unsafe_payload)


def test_payload_rejects_self_consistent_status_and_value_surface_tampering() -> None:
    report = build_research_event_claim_resolution_authority_lag_report(
        (candidate(),),
        generated_at=GENERATED_AT,
        config=ResearchEventClaimResolutionAuthorityLagConfig(),
    )
    payload = research_event_claim_resolution_authority_lag_report_payload(report)

    invalid_summary_status = _with_recomputed_digest({**payload, "status": "review"})
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        research_event_claim_resolution_authority_lag_report_payload(invalid_summary_status)

    invalid_row_status = _json_clone(payload)
    invalid_row_status["rows"][0]["lag_status"] = "review"  # type: ignore[index]
    with pytest.raises(ValueError, match="lag_status must be one of pass, watch, block"):
        research_event_claim_resolution_authority_lag_report_payload(
            _with_recomputed_digest(invalid_row_status),
        )

    unsafe_value = _with_recomputed_digest({**payload, "public_note": "submit_order_signal"})
    with pytest.raises(ValueError, match="unsafe public payload value"):
        research_event_claim_resolution_authority_lag_report_payload(unsafe_value)


def test_public_labels_reject_raw_text_and_surface_fragments() -> None:
    with pytest.raises(ValueError, match="claim_category"):
        candidate(claim_category="Will this leak question text?")

    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=("raw-market-slug",))

    with pytest.raises(ValueError, match="unsafe public payload value"):
        candidate(reason_codes=("source_text",))


def test_validation_rejects_invalid_decimals_datetimes_flags_and_subclasses() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_claim_resolution_authority_lag_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
            config=ResearchEventClaimResolutionAuthorityLagConfig(),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 9, 11, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 9, 11, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        candidate(observed_at=DatetimeSubclass(2026, 7, 9, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="resolver_confirmation_count"):
        candidate(resolver_confirmation_count=Decimal("-1"))
    with pytest.raises(ValueError, match="authority_reported_at"):
        candidate(authority_reported_at=RESOLUTION_AT - timedelta(hours=1))
    with pytest.raises(ValueError, match="watch_lag_hours"):
        ResearchEventClaimResolutionAuthorityLagConfig(
            watch_lag_hours=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="block_lag_hours"):
        ResearchEventClaimResolutionAuthorityLagConfig(
            watch_lag_hours=Decimal("48"),
            block_lag_hours=Decimal("24"),
        )
    with pytest.raises(ValueError, match="report_only"):
        dataclasses.replace(ResearchEventClaimResolutionAuthorityLagConfig(), report_only=False)

    config = ResearchEventClaimResolutionAuthorityLagConfig()
    input_row = candidate()
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.candidate_id = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchEventClaimResolutionAuthorityLagConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class CandidateSubclass(ResearchEventClaimResolutionAuthorityLagCandidate):
            pass


def test_static_module_has_no_forbidden_side_effect_imports_or_public_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_claim_resolution_authority_lag_report.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "web3",
    }
    public_surface_forbidden_fragments = (
        "wallet",
        "private_key",
        "token",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports

    namespace: dict[str, object] = {}
    exec(compile(tree, "<module>", "exec"), namespace)
    exported = namespace["__all__"]
    assert isinstance(exported, tuple)
    assert not [
        name
        for name in exported
        for fragment in public_surface_forbidden_fragments
        if fragment in name.lower()
    ]


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)


def _json_clone(value: dict[str, object]) -> dict[str, object]:
    return json.loads(json.dumps(value, sort_keys=True))


def _with_recomputed_digest(payload: dict[str, object]) -> dict[str, object]:
    payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            {
                key: value
                for key, value in payload.items()
                if key != "derived_validation_digest"
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    return payload
