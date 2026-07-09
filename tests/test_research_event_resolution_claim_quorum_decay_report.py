from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab.research_event_resolution_claim_quorum_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest_ref(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def claim_input(**overrides: object) -> Any:
    module = api()
    values = {
        "event_ref_digest": digest_ref("event-alpha"),
        "claim_ref_digest": digest_ref("claim-alpha"),
        "event_category": "politics",
        "claim_observed_at": GENERATED_AT - timedelta(hours=12),
        "last_verified_at": GENERATED_AT - timedelta(minutes=30),
        "active_independent_source_count": d("4.000000"),
        "stale_independent_source_count": d("0.000000"),
        "contradicted_independent_source_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchEventResolutionClaimQuorumDecayInput(**values)


def report(rows: list[object] | tuple[object, ...], *, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_event_resolution_claim_quorum_decay_report(
        rows,
        config=cfg or module.ResearchEventResolutionClaimQuorumDecayConfig(),
        generated_at=GENERATED_AT,
    )


def test_report_sorts_rows_and_rolls_up_block_watch_and_pass_statuses() -> None:
    module = api()
    blocked = claim_input(
        event_ref_digest=digest_ref("event-block"),
        claim_ref_digest=digest_ref("claim-block"),
        event_category="sports",
        claim_observed_at=GENERATED_AT - timedelta(days=4),
        last_verified_at=None,
        active_independent_source_count=d("1.000000"),
        stale_independent_source_count=d("2.000000"),
    )
    watched = claim_input(
        event_ref_digest=digest_ref("event-watch"),
        claim_ref_digest=digest_ref("claim-watch"),
        event_category="economics",
        claim_observed_at=GENERATED_AT - timedelta(days=2),
        last_verified_at=GENERATED_AT - timedelta(hours=2),
        active_independent_source_count=d("3.000000"),
        stale_independent_source_count=d("1.000000"),
    )
    passed = claim_input(
        event_ref_digest=digest_ref("event-pass"),
        claim_ref_digest=digest_ref("claim-pass"),
        event_category="politics",
    )

    decay_report = report([passed, watched, blocked])
    repeated_report = report([blocked, passed, watched])

    assert type(decay_report) is module.ResearchEventResolutionClaimQuorumDecayReport
    assert is_dataclass(decay_report)
    assert decay_report.__dataclass_params__.frozen
    assert decay_report.generated_at == GENERATED_AT
    assert decay_report.config_version == (
        module.DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_QUORUM_DECAY_REPORT_CONFIG_VERSION
    )
    assert decay_report.report_status == "block"
    assert decay_report.claim_count == d("3.000000")
    assert decay_report.pass_count == d("1.000000")
    assert decay_report.watch_count == d("1.000000")
    assert decay_report.block_count == d("1.000000")
    assert decay_report.missing_verification_count == d("1.000000")
    assert decay_report.below_quorum_count == d("1.000000")
    assert decay_report.contradicted_claim_count == d("0.000000")
    assert decay_report.stale_verification_count == d("0.000000")
    assert decay_report.max_quorum_decay_score == d("0.666667")
    assert decay_report.total_active_independent_source_count == d("8.000000")
    assert decay_report.total_stale_independent_source_count == d("3.000000")
    assert decay_report.total_contradicted_independent_source_count == d("0.000000")
    assert [row.status for row in decay_report.rows] == ["block", "watch", "pass"]
    assert decay_report.rows[0].claim_age_seconds == d("345600.000000")
    assert decay_report.rows[0].last_verified_age_seconds is None
    assert decay_report.rows[0].active_quorum_ratio == d("0.333333")
    assert decay_report.rows[0].quorum_decay_score == d("0.666667")
    assert decay_report.rows[0].reason_codes == (
        "resolution_claim_quorum_decay_block",
        "missing_claim_verification_timestamp",
        "active_independent_source_quorum_below_required",
        "high_resolution_claim_quorum_decay",
    )
    assert decay_report.rows[1].status == "watch"
    assert decay_report.rows[1].active_quorum_ratio == d("1.000000")
    assert decay_report.rows[1].quorum_decay_score == d("0.250000")
    assert decay_report.rows[1].reason_codes == (
        "resolution_claim_quorum_decay_watch",
        "medium_resolution_claim_quorum_decay",
        "active_independent_source_quorum_at_floor",
    )
    assert decay_report.rows[2].status == "pass"
    assert decay_report.rows[2].reason_codes == ("resolution_claim_quorum_decay_pass",)
    assert decay_report.derived_validation_digest == (
        repeated_report.derived_validation_digest
    )
    assert len(decay_report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in decay_report.derived_validation_digest
    )
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True


def test_empty_input_blocks_with_zero_decimal_rollups() -> None:
    module = api()

    decay_report = report([])

    assert decay_report.report_status == "block"
    assert decay_report.rows == ()
    assert decay_report.claim_count == d("0.000000")
    assert decay_report.pass_count == d("0.000000")
    assert decay_report.watch_count == d("0.000000")
    assert decay_report.block_count == d("0.000000")
    assert decay_report.missing_verification_count == d("0.000000")
    assert decay_report.below_quorum_count == d("0.000000")
    assert decay_report.contradicted_claim_count == d("0.000000")
    assert decay_report.stale_verification_count == d("0.000000")
    assert decay_report.max_quorum_decay_score == d("0.000000")
    assert decay_report.total_active_independent_source_count == d("0.000000")
    assert decay_report.total_stale_independent_source_count == d("0.000000")
    assert decay_report.total_contradicted_independent_source_count == d("0.000000")
    assert decay_report.reason_code_counts == (
        module.ResearchEventResolutionClaimQuorumDecayReasonCodeCount(
            reason_code="resolution_claim_quorum_decay_empty",
            row_count=d("1.000000"),
        ),
    )


def test_custom_required_quorum_config_drives_ratio_and_reasons() -> None:
    module = api()
    cfg = module.ResearchEventResolutionClaimQuorumDecayConfig(
        required_active_independent_source_count=d("4.000000"),
    )

    decay_report = report(
        [
            claim_input(
                active_independent_source_count=d("3.000000"),
                stale_independent_source_count=d("0.000000"),
            ),
        ],
        cfg=cfg,
    )

    assert decay_report.report_status == "block"
    assert decay_report.below_quorum_count == d("1.000000")
    assert decay_report.rows[0].required_active_independent_source_count == d("4.000000")
    assert decay_report.rows[0].active_quorum_ratio == d("0.750000")
    assert decay_report.rows[0].reason_codes == (
        "resolution_claim_quorum_decay_block",
        "active_independent_source_quorum_below_required",
    )
    with pytest.raises(ValueError, match="active_quorum_ratio"):
        replace(
            decay_report.rows[0],
            active_quorum_ratio=d("0.500000"),
            derived_validation_digest="",
        )


def test_contradictions_block_and_payload_is_safe_json_without_raw_identifiers() -> None:
    module = api()
    raw_fragments = (
        "candidate-alpha",
        "market-alpha",
        "will-this-resolve",
        "https://example.test/source",
        "raw source text",
        "postgresql://example.test/db",
        "paper_resolution_claims",
        "wallet",
        "order",
        "trade",
        "position-sizing",
        "recommendation",
    )
    decay_report = report(
        [
            claim_input(
                event_ref_digest=digest_ref(raw_fragments[1]),
                claim_ref_digest=digest_ref(raw_fragments[0]),
                contradicted_independent_source_count=d("1.000000"),
            ),
        ],
    )

    assert decay_report.report_status == "block"
    assert decay_report.block_count == d("1.000000")
    assert decay_report.contradicted_claim_count == d("1.000000")
    assert decay_report.rows[0].reason_codes == (
        "resolution_claim_quorum_decay_block",
        "contradicted_resolution_claim_sources_present",
    )

    payload = module.research_event_resolution_claim_quorum_decay_report_payload(
        decay_report,
    )
    encoded = json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["claim_count"] == "1.000000"
    assert payload["rows"][0]["claim_age_seconds"] == "43200.000000"
    assert payload["rows"][0]["quorum_decay_score"] == "0.200000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _contains_float(payload)
    for raw_fragment in raw_fragments:
        assert raw_fragment not in encoded
    assert module.validate_research_event_resolution_claim_quorum_decay_public_payload(
        payload,
    )
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["claim_count"] = "9.000000"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]
    unsafe_payload = dict(payload)
    unsafe_payload["candidate_id"] = "candidate-alpha"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_event_resolution_claim_quorum_decay_public_payload(
            unsafe_payload,
        )


def test_validation_is_strict_frozen_digest_backed_and_paper_only() -> None:
    module = api()
    row = claim_input()
    other_row = claim_input(
        event_ref_digest=digest_ref("event-beta"),
        claim_ref_digest=digest_ref("claim-beta"),
    )
    decay_report = report([row, other_row])

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_QUORUM_DECAY_REPORT_CONFIG_VERSION",
        "ResearchEventResolutionClaimQuorumDecayConfig",
        "ResearchEventResolutionClaimQuorumDecayInput",
        "ResearchEventResolutionClaimQuorumDecayRow",
        "ResearchEventResolutionClaimQuorumDecayReasonCodeCount",
        "ResearchEventResolutionClaimQuorumDecayReport",
        "build_research_event_resolution_claim_quorum_decay_report",
        "research_event_resolution_claim_quorum_decay_report_payload",
        "validate_research_event_resolution_claim_quorum_decay_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        row.event_ref_digest = digest_ref("changed")  # type: ignore[misc]
    with pytest.raises(ValueError, match="event_ref_digest"):
        claim_input(event_ref_digest=_StringSubclass(digest_ref("event-subclass")))
    with pytest.raises(ValueError, match="event_ref_digest"):
        claim_input(event_ref_digest="event-alpha")
    with pytest.raises(ValueError, match="active_independent_source_count"):
        claim_input(active_independent_source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_independent_source_count"):
        claim_input(stale_independent_source_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="contradicted_independent_source_count"):
        claim_input(contradicted_independent_source_count=d("0.500000"))
    with pytest.raises(ValueError, match="claim_observed_at"):
        claim_input(claim_observed_at=datetime(2026, 7, 7, 10, 0))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_event_resolution_claim_quorum_decay_report(
            [row],
            config=module.ResearchEventResolutionClaimQuorumDecayConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="claim_observed_at"):
        report([claim_input(claim_observed_at=GENERATED_AT + timedelta(seconds=1))])
    with pytest.raises(ValueError, match="last_verified_at"):
        report(
            [
                claim_input(
                    claim_observed_at=GENERATED_AT - timedelta(hours=1),
                    last_verified_at=GENERATED_AT - timedelta(hours=2),
                ),
            ],
        )
    with pytest.raises(ValueError, match="claim_ref_digest"):
        report([row, row])
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(decay_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(decay_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(decay_report.rows[0], status="empty", derived_validation_digest="")
    with pytest.raises(ValueError, match="report_status"):
        replace(decay_report, report_status="empty", derived_validation_digest="")


def test_source_file_exposes_no_live_capability_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_resolution_claim_quorum_decay_report.py"
    )
    tree = ast.parse(source_path.read_text())
    banned_fragments = (
        "network",
        "socket",
        "requests",
        "http",
        "auth",
        "wallet",
        "account",
        "broker",
        "trade",
        "trading",
        "order",
        "database",
        "db",
        "dsn",
        "token",
        "recommendation",
        "sizing",
        "market_id",
        "market_slug",
        "market_question",
        "candidate_id",
        "source_url",
        "source_text",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in banned_fragments)
        if isinstance(node, ast.arg):
            lowered = node.arg.lower()
            assert not any(fragment in lowered for fragment in banned_fragments)


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False
