from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_claim_freshness_evidence_router_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(seconds: int) -> datetime:
    return NOW - timedelta(seconds=seconds)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-source-claim-freshness-evidence-router-report-v0",
        "watch_claim_age_seconds": d("21600.000000"),
        "block_claim_age_seconds": d("86400.000000"),
        "max_fresh_evidence_age_seconds": d("7200.000000"),
        "block_evidence_age_seconds": d("21600.000000"),
        "min_fresh_evidence_count": d("2"),
        "min_source_family_count": d("2"),
        "watch_contradiction_pressure": d("0.250000"),
        "block_contradiction_pressure": d("0.750000"),
    }
    values.update(overrides)
    return module.ResearchSourceClaimFreshnessEvidenceRouterConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "claim_bucket": "claim_pass",
        "source_family": "official",
        "claim_observed_at": ago(1800),
        "evidence_observed_at": ago(600),
        "evidence_position": "supports",
    }
    values.update(overrides)
    return module.ResearchSourceClaimFreshnessEvidenceRouterObservation(**values)


def report(*rows, cfg=None, generated_at: datetime = NOW):
    module = api()
    return module.build_research_source_claim_freshness_evidence_router_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float(item)
    else:
        assert type(value) is not float


def test_routes_claim_freshness_evidence_by_status_and_sorts_deterministically() -> None:
    observations = (
        observation(claim_bucket="claim_pass", source_family="official"),
        observation(claim_bucket="claim_pass", source_family="archive"),
        observation(
            claim_bucket="claim_watch",
            source_family="official",
            claim_observed_at=ago(28800),
            evidence_observed_at=ago(9000),
            evidence_position="contradicts",
        ),
        observation(
            claim_bucket="claim_watch",
            source_family="archive",
            claim_observed_at=ago(3600),
            evidence_observed_at=ago(3000),
        ),
        observation(
            claim_bucket="claim_block",
            source_family="official",
            claim_observed_at=ago(90000),
            evidence_observed_at=ago(30000),
            evidence_position="contradicts",
        ),
    )
    routed = report(*observations)
    reversed_report = report(*reversed(observations))

    assert routed.generated_at == NOW
    assert routed.claim_bucket_count == d("3")
    assert routed.evidence_count == d("5")
    assert routed.pass_count == d("1")
    assert routed.watch_count == d("1")
    assert routed.block_count == d("1")
    assert routed.stale_evidence_count == d("2")
    assert routed.max_claim_age_seconds == d("90000.000000")
    assert routed.max_evidence_age_seconds == d("30000.000000")
    assert routed.max_contradiction_pressure == d("1.000000")
    assert routed.status == "block"
    assert routed.paper_only is True
    assert routed.report_only is True
    assert routed.readonly is True
    assert tuple(row.claim_bucket for row in routed.rows) == (
        "claim_block",
        "claim_watch",
        "claim_pass",
    )
    assert tuple(row.claim_bucket for row in reversed_report.rows) == (
        "claim_block",
        "claim_watch",
        "claim_pass",
    )

    block_row = routed.rows[0]
    assert block_row.status == "block"
    assert block_row.evidence_count == d("1")
    assert block_row.source_family_count == d("1")
    assert block_row.fresh_evidence_count == d("0")
    assert block_row.stale_evidence_count == d("1")
    assert block_row.max_claim_age_seconds == d("90000.000000")
    assert block_row.max_evidence_age_seconds == d("30000.000000")
    assert block_row.fresh_evidence_ratio == d("0.000000")
    assert block_row.contradiction_pressure == d("1.000000")
    assert block_row.reason_codes == (
        "claim_age_block",
        "evidence_age_block",
        "fresh_evidence_quorum_block",
        "source_family_quorum_block",
        "contradiction_pressure_block",
    )

    watch_row = routed.rows[1]
    assert watch_row.status == "watch"
    assert watch_row.evidence_count == d("2")
    assert watch_row.source_family_count == d("2")
    assert watch_row.fresh_evidence_count == d("1")
    assert watch_row.stale_evidence_count == d("1")
    assert watch_row.max_claim_age_seconds == d("28800.000000")
    assert watch_row.max_evidence_age_seconds == d("9000.000000")
    assert watch_row.fresh_evidence_ratio == d("0.500000")
    assert watch_row.contradiction_pressure == d("0.500000")
    assert watch_row.reason_codes == (
        "claim_age_watch",
        "evidence_age_watch",
        "fresh_evidence_quorum_watch",
        "contradiction_pressure_watch",
    )

    pass_row = routed.rows[2]
    assert pass_row.status == "pass"
    assert pass_row.evidence_count == d("2")
    assert pass_row.source_family_count == d("2")
    assert pass_row.fresh_evidence_count == d("2")
    assert pass_row.stale_evidence_count == d("0")
    assert pass_row.fresh_evidence_ratio == d("1.000000")
    assert pass_row.reason_codes == ("freshness_evidence_router_pass",)


def test_public_payload_is_deterministic_decimal_only_and_digest_validated() -> None:
    module = api()
    routed = report(
        observation(claim_bucket="claim_watch", source_family="official"),
        observation(claim_bucket="claim_watch", source_family="archive"),
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.research_source_claim_freshness_evidence_router_report_payload(routed)
    payload_without_digest = dict(payload)
    digest_value = payload_without_digest.pop("derived_validation_digest")
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert payload == routed.payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["claim_bucket_count"] == "1"
    assert payload["evidence_count"] == "2"
    assert payload["rows"][0]["claim_bucket"] == "claim_watch"
    assert payload["rows"][0]["fresh_evidence_ratio"] == "1.000000"
    assert routed.derived_validation_digest == digest_value
    assert sha256(canonical.encode("utf-8")).hexdigest() == digest_value
    assert "Decimal(" not in repr(payload)
    assert "datetime" not in encoded
    for unsafe in (
        "candidate",
        "market",
        "slug",
        "question",
        "http",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
    ):
        assert unsafe not in encoded
    assert_no_float(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(routed, derived_validation_digest="0" * 64)


def test_validates_decimal_datetime_status_flags_and_public_identifiers() -> None:
    module = api()
    routed = report(observation(), observation(source_family="archive"))

    assert module.STATUSES == ("pass", "watch", "block")
    with pytest.raises(FrozenInstanceError):
        routed.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="claim_observed_at must be a datetime"):
        observation(claim_observed_at=_DatetimeSubclass(2026, 7, 8, 11, tzinfo=UTC))

    with pytest.raises(ValueError, match="claim_observed_at must be timezone-aware"):
        observation(claim_observed_at=datetime(2026, 7, 8, 11, tzinfo=_NoneOffsetTimezone()))

    with pytest.raises(ValueError, match="min_fresh_evidence_count must be a Decimal"):
        config(min_fresh_evidence_count=2)

    with pytest.raises(ValueError, match="min_fresh_evidence_count must be a Decimal"):
        config(min_fresh_evidence_count=_DecimalSubclass("2"))

    with pytest.raises(ValueError, match="watch_claim_age_seconds must be finite"):
        config(watch_claim_age_seconds=Decimal("NaN"))

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="research-source-claim-freshness-evidence-router-report-v1")

    for unsafe_bucket in (
        "candidate_alpha",
        "market_alpha",
        "slug_alpha",
        "question_alpha",
        "http_alpha",
        "url_alpha",
        "text_alpha",
        "dsn_alpha",
        "table_alpha",
        "token_alpha",
        "wallet_alpha",
        "order_alpha",
        "trade_alpha",
        "auth_alpha",
    ):
        with pytest.raises(ValueError, match="claim_bucket has unsafe public value"):
            observation(claim_bucket=unsafe_bucket)

    with pytest.raises(ValueError, match="config must be readonly"):
        config(readonly=False)

    with pytest.raises(ValueError, match="observation must be paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="status"):
        replace(routed.rows[0], status="blocked")

    with pytest.raises(ValueError, match="evidence_count"):
        replace(routed, evidence_count=d("3"))


def test_rejects_temporal_inconsistency_empty_inputs_and_bad_positions() -> None:
    with pytest.raises(ValueError, match="observations must not be empty"):
        report()

    with pytest.raises(ValueError, match="claim_observed_at must not be after generated_at"):
        report(
            observation(
                claim_observed_at=NOW + timedelta(seconds=1),
                evidence_observed_at=NOW + timedelta(seconds=2),
            ),
        )

    with pytest.raises(ValueError, match="evidence_observed_at must not be before claim_observed_at"):
        observation(
            claim_observed_at=ago(3600),
            evidence_observed_at=ago(7200),
        )

    with pytest.raises(ValueError, match="evidence_position"):
        observation(evidence_position="unknown")


def test_module_scope_has_no_forbidden_runtime_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_source_claim_freshness_evidence_router_report.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlite",
        "supabase",
    )
    forbidden_runtime_names = (
        "wallet",
        "signing",
        "private_key",
        "api_key",
        "auth",
        "token",
        "dsn",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "submit",
        "cancel",
        "replace_order",
        "create_order",
        "execute",
        "connect",
        "commit",
        "rollback",
        "cursor",
        "open",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", maxsplit=1)[0] not in forbidden_modules
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", maxsplit=1)[0] not in forbidden_modules
        if isinstance(node, ast.Name):
            assert node.id.lower() not in forbidden_runtime_names
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in forbidden_runtime_names
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "float"
                assert node.func.id.lower() not in forbidden_runtime_names
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr.lower() not in forbidden_runtime_names


def test_elapsed_time_uses_decimal_safe_datetime_arithmetic() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_source_claim_freshness_evidence_router_report.py",
    ).read_text(encoding="utf-8")

    assert ".timestamp(" not in source
    assert ".total_seconds(" not in source
