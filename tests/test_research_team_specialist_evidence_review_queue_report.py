from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)
SHA_A = "sha256:" + ("a" * 64)
SHA_B = "sha256:" + ("b" * 64)
SHA_C = "sha256:" + ("c" * 64)
BUNDLE_A = "sha256:" + ("1" * 64)
BUNDLE_B = "sha256:" + ("2" * 64)
BUNDLE_C = "sha256:" + ("3" * 64)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_evidence_review_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _strip_digest_fields(value: Any) -> Any:
    if type(value) is dict:
        return {
            key: _strip_digest_fields(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_strip_digest_fields(item) for item in value]
    return value


def canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        _strip_digest_fields(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "queue_watch_age_seconds": d("3600.000000"),
        "queue_block_age_seconds": d("10800.000000"),
        "evidence_watch_age_seconds": d("86400.000000"),
        "evidence_block_age_seconds": d("259200.000000"),
        "min_pass_source_family_count": d("3"),
        "unresolved_watch_claim_count": d("1"),
        "unresolved_block_claim_count": d("3"),
        "contradiction_watch_count": d("1"),
        "contradiction_block_count": d("2"),
        "stale_source_watch_count": d("1"),
        "stale_source_block_count": d("3"),
        "min_reviewer_available_count": d("1"),
        "complexity_watch_score": d("0.500000"),
        "complexity_block_score": d("0.800000"),
        "queue_age_weight": d("0.200000"),
        "evidence_age_weight": d("0.150000"),
        "source_family_weight": d("0.150000"),
        "unresolved_claim_weight": d("0.150000"),
        "contradiction_weight": d("0.150000"),
        "stale_source_weight": d("0.100000"),
        "reviewer_capacity_weight": d("0.050000"),
        "complexity_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistEvidenceReviewQueueReportConfig(**values)


def queue_item(
    team_ref: str,
    specialist_ref: str,
    evidence_digest: str,
    bundle_digest: str,
    *,
    queued_seconds_ago: int,
    evidence_age_seconds: int,
    source_families: str,
    unresolved_claims: str,
    contradictions: str,
    stale_sources: str,
    reviewer_available: str,
    complexity: str,
):
    module = api()
    return module.ResearchTeamSpecialistEvidenceReviewQueueItem(
        team_ref=team_ref,
        specialist_ref=specialist_ref,
        evidence_packet_digest=evidence_digest,
        source_bundle_digest=bundle_digest,
        queued_at=GENERATED_AT - timedelta(seconds=queued_seconds_ago),
        evidence_observed_at=GENERATED_AT - timedelta(seconds=evidence_age_seconds),
        source_family_count=d(source_families),
        unresolved_claim_count=d(unresolved_claims),
        contradiction_count=d(contradictions),
        stale_source_count=d(stale_sources),
        reviewer_available_count=d(reviewer_available),
        review_complexity_score=d(complexity),
    )


def build_report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_specialist_evidence_review_queue_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def pass_item():
    return queue_item(
        "team-alpha",
        "specialist-macro",
        SHA_A,
        BUNDLE_A,
        queued_seconds_ago=600,
        evidence_age_seconds=3600,
        source_families="4",
        unresolved_claims="0",
        contradictions="0",
        stale_sources="0",
        reviewer_available="2",
        complexity="0.100000",
    )


def watch_item():
    return queue_item(
        "team-alpha",
        "specialist-rates",
        SHA_B,
        BUNDLE_B,
        queued_seconds_ago=7200,
        evidence_age_seconds=100000,
        source_families="2",
        unresolved_claims="1",
        contradictions="1",
        stale_sources="1",
        reviewer_available="1",
        complexity="0.600000",
    )


def block_item():
    return queue_item(
        "team-beta",
        "specialist-weather",
        SHA_C,
        BUNDLE_C,
        queued_seconds_ago=12000,
        evidence_age_seconds=300000,
        source_families="0",
        unresolved_claims="4",
        contradictions="2",
        stale_sources="3",
        reviewer_available="0",
        complexity="0.900000",
    )


def assert_decimal_only_numerics(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_decimal_only_numerics(item)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_values(item)


def test_scores_and_prioritizes_evidence_review_queue() -> None:
    module = api()

    report = build_report(pass_item(), block_item(), watch_item())

    assert module.RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.item_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.stale_evidence_count == d("2")
    assert report.source_family_gap_count == d("2")
    assert report.total_unresolved_claim_count == d("5")
    assert report.total_contradiction_count == d("3")
    assert report.total_stale_source_count == d("4")
    assert report.reviewer_capacity_gap_count == d("1")
    assert report.max_review_priority_score == d("0.995000")
    assert report.average_review_priority_score == d("0.480911")

    blocked, watched, passed = report.rows
    assert (blocked.team_ref, blocked.specialist_ref) == (
        "team-beta",
        "specialist-weather",
    )
    assert blocked.queue_age_component == d("1.000000")
    assert blocked.evidence_age_component == d("1.000000")
    assert blocked.source_family_gap == d("1.000000")
    assert blocked.unresolved_claim_component == d("1.000000")
    assert blocked.contradiction_component == d("1.000000")
    assert blocked.stale_source_component == d("1.000000")
    assert blocked.reviewer_capacity_gap == d("1.000000")
    assert blocked.review_priority_score == d("0.995000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "queue_age_block",
        "evidence_age_block",
        "source_family_gap_block",
        "unresolved_claims_block",
        "contradiction_block",
        "stale_source_block",
        "reviewer_capacity_block",
        "complexity_block",
    )

    assert (watched.team_ref, watched.specialist_ref) == (
        "team-alpha",
        "specialist-rates",
    )
    assert watched.review_priority_score == d("0.429537")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "queue_age_watch",
        "evidence_age_watch",
        "source_family_gap_watch",
        "unresolved_claims_watch",
        "contradiction_watch",
        "stale_source_watch",
        "complexity_watch",
    )

    assert (passed.team_ref, passed.specialist_ref) == (
        "team-alpha",
        "specialist-macro",
    )
    assert passed.review_priority_score == d("0.018195")
    assert passed.status == "pass"
    assert passed.reason_codes == ("evidence_review_queue_pass",)
    assert report.reason_codes == (
        "queue_age_block",
        "evidence_age_block",
        "source_family_gap_block",
        "unresolved_claims_block",
        "contradiction_block",
        "stale_source_block",
        "reviewer_capacity_block",
        "complexity_block",
        "queue_age_watch",
        "evidence_age_watch",
        "source_family_gap_watch",
        "unresolved_claims_watch",
        "contradiction_watch",
        "stale_source_watch",
        "complexity_watch",
    )
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_only_numerics(report)


def test_custom_valid_weights_are_supported_and_deterministic() -> None:
    module = api()
    cfg = config(
        queue_age_weight=d("0.100000"),
        evidence_age_weight=d("0.250000"),
    )

    report_a = build_report(watch_item(), cfg=cfg)
    report_b = build_report(watch_item(), cfg=cfg)
    payload_a = module.research_team_specialist_evidence_review_queue_report_payload(
        report_a,
    )
    payload_b = module.research_team_specialist_evidence_review_queue_report_payload(
        report_b,
    )

    assert report_a.rows[0].review_priority_score == d("0.401450")
    assert report_a == report_b
    assert payload_a == payload_b
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)


def test_empty_queue_passes_without_live_or_action_surface() -> None:
    module = api()

    report = build_report()

    assert report.status == "pass"
    assert report.item_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.rows == ()
    assert report.max_review_priority_score == d("0.000000")
    assert report.average_review_priority_score == d("0.000000")
    assert report.reason_codes == ("evidence_review_queue_empty",)
    assert report.reason_code_counts == (
        module.ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount(
            reason_code="evidence_review_queue_empty",
            count=d("1"),
        ),
    )
    assert_decimal_only_numerics(report)


def test_payload_is_deterministic_decimal_string_only_and_tamper_evident() -> None:
    module = api()
    first = watch_item()
    second = block_item()

    report_a = build_report(first, second)
    report_b = build_report(second, first)
    payload = module.research_team_specialist_evidence_review_queue_report_payload(report_a)
    reversed_payload = module.research_team_specialist_evidence_review_queue_report_payload(
        report_b,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert report_a.rows == report_b.rows
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload == reversed_payload
    assert payload["generated_at"] == "2026-07-09T14:00:00+00:00"
    assert payload["item_count"] == "2"
    assert payload["rows"][0]["evidence_packet_digest"] == SHA_C
    assert payload["rows"][0]["derived_validation_digest"] == (
        report_a.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.research_team_specialist_evidence_review_queue_report_digest(report_a) == (
        payload["derived_validation_digest"]
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    json.loads(encoded)

    leaked_fragments = (
        "candidate-raw-123",
        "market-slug",
        "will-this-happen",
        "https://example.test/source",
        "postgres://",
        "secret-token",
        "wallet",
        "order",
        "trade",
    )
    assert not any(fragment in encoded for fragment in leaked_fragments)

    tampered = dict(payload)
    tampered["block_count"] = "7"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_evidence_review_queue_report_payload(tampered)

    object.__setattr__(report_a.rows[0], "review_priority_score", d("0.000001"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_team_specialist_evidence_review_queue_report_payload(report_a)

    with pytest.raises(ValueError, match="Decimal"):
        module.research_team_specialist_evidence_review_queue_report_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="float"):
        module.research_team_specialist_evidence_review_queue_report_payload(
            {"score": 0.5, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_evidence_review_queue_report_payload(
            {
                "candidate_id": "candidate-raw-123",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_evidence_review_queue_report_payload(
            {
                "note": "https://example.test/source",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    for payload, error_match in (
        (
            {
                "status": "execute",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
            "status",
        ),
        (
            {
                "nested": {"readonly": False},
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
            "readonly",
        ),
        (
            {
                "rows": (),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
            "JSON",
        ),
        (
            {
                "action": "execute",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
            "unsafe public",
        ),
    ):
        payload["derived_validation_digest"] = canonical_digest(payload)
        with pytest.raises(ValueError, match=error_match):
            module.research_team_specialist_evidence_review_queue_report_payload(payload)


def test_validation_rejects_bad_types_dates_flags_and_duplicate_digests() -> None:
    module = api()
    item = watch_item()
    report = build_report(item)

    for value in (config(), item, report.rows[0], report.reason_code_counts[0], report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="source_family_count"):
        replace(item, source_family_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="review_complexity_score"):
        replace(item, review_complexity_score=d("1.000001"))
    with pytest.raises(ValueError, match="evidence_packet_digest"):
        replace(item, evidence_packet_digest="candidate-raw-123")
    with pytest.raises(ValueError, match="weights"):
        config(queue_age_weight=d("0.300000"))
    with pytest.raises(ValueError, match="queue_block_age_seconds"):
        config(queue_block_age_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(item, generated_at=datetime(2026, 7, 9, 14, 0))

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(
            item,
            generated_at=datetime(2026, 7, 9, 14, 0, tzinfo=MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="queued_at must not be in the future"):
        build_report(
            module.ResearchTeamSpecialistEvidenceReviewQueueItem(
                team_ref="team-alpha",
                specialist_ref="specialist-rates",
                evidence_packet_digest=SHA_A,
                source_bundle_digest=BUNDLE_A,
                queued_at=GENERATED_AT + timedelta(seconds=1),
                evidence_observed_at=GENERATED_AT,
                source_family_count=d("1"),
                unresolved_claim_count=d("0"),
                contradiction_count=d("0"),
                stale_source_count=d("0"),
                reviewer_available_count=d("1"),
                review_complexity_score=d("0.100000"),
            ),
        )
    with pytest.raises(ValueError, match="repeat evidence packet digests"):
        build_report(item, item)

    blocked_report = build_report(block_item())
    for field_name in (
        "stale_evidence_count",
        "source_family_gap_count",
        "reviewer_capacity_gap_count",
    ):
        with pytest.raises(ValueError, match=field_name):
            replace(
                blocked_report,
                **{field_name: d("0"), "derived_validation_digest": ""},
            )


def test_module_scope_has_no_db_network_wallet_order_sizing_or_live_surface() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_REPORT_CONFIG_VERSION",
        "RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_STATUSES",
        "ResearchTeamSpecialistEvidenceReviewQueueReportConfig",
        "ResearchTeamSpecialistEvidenceReviewQueueItem",
        "ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount",
        "ResearchTeamSpecialistEvidenceReviewQueueRow",
        "ResearchTeamSpecialistEvidenceReviewQueueReport",
        "build_research_team_specialist_evidence_review_queue_report",
        "research_team_specialist_evidence_review_queue_report_digest",
        "research_team_specialist_evidence_review_queue_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "private_key",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "execute",
        "execution",
        "auth",
        "live",
        "network",
        "connect(",
        "open(",
        "subprocess",
        "pathlib",
    )
    lowered = source_text.lower()
    assert all(term not in lowered for term in forbidden_source_terms)
