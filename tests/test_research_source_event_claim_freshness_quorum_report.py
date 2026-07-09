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


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_event_claim_freshness_quorum_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-source-event-claim-freshness-quorum-v0",
        "watch_fresh_source_quorum": d("2"),
        "block_fresh_source_quorum": d("0"),
        "watch_primary_fresh_source_quorum": d("1"),
        "block_primary_fresh_source_quorum": d("0"),
        "watch_latest_verification_age_seconds": d("7200.000000"),
        "block_latest_verification_age_seconds": d("21600.000000"),
        "watch_stale_source_ratio": d("0.500000"),
        "block_stale_source_ratio": d("0.800000"),
        "watch_source_agreement_score": d("0.700000"),
        "block_source_agreement_score": d("0.400000"),
        "watch_contradiction_pressure": d("0.300000"),
        "block_contradiction_pressure": d("0.600000"),
        "watch_extraction_confidence": d("0.800000"),
        "block_extraction_confidence": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourceEventClaimFreshnessQuorumConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "event_claim_bucket": "official-policy",
        "source_family_count": d("4"),
        "fresh_source_count": d("3"),
        "primary_fresh_source_count": d("2"),
        "latest_verified_at": ago(1800),
        "source_agreement_score": d("0.900000"),
        "contradiction_pressure": d("0.050000"),
        "extraction_confidence": d("0.920000"),
    }
    values.update(overrides)
    return module.ResearchSourceEventClaimFreshnessQuorumObservation(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_source_event_claim_freshness_quorum_report(
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


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_builds_event_claim_freshness_quorum_report_from_public_inputs() -> None:
    freshness_report = report(
        observation(event_claim_bucket="official-policy"),
        observation(
            event_claim_bucket="regional-board",
            fresh_source_count=d("1"),
            primary_fresh_source_count=d("1"),
            latest_verified_at=ago(10800),
            source_agreement_score=d("0.600000"),
            contradiction_pressure=d("0.350000"),
            extraction_confidence=d("0.700000"),
        ),
        observation(
            event_claim_bucket="thin-feed",
            source_family_count=d("5"),
            fresh_source_count=d("0"),
            primary_fresh_source_count=d("0"),
            latest_verified_at=ago(28800),
            source_agreement_score=d("0.300000"),
            contradiction_pressure=d("0.800000"),
            extraction_confidence=d("0.400000"),
        ),
    )

    assert freshness_report.generated_at == GENERATED_AT
    assert freshness_report.event_claim_bucket_count == d("3")
    assert freshness_report.pass_count == d("1")
    assert freshness_report.watch_count == d("1")
    assert freshness_report.block_count == d("1")
    assert freshness_report.min_fresh_source_count == d("0")
    assert freshness_report.min_primary_fresh_source_count == d("0")
    assert freshness_report.max_latest_verification_age_seconds == d("28800.000000")
    assert freshness_report.max_stale_source_ratio == d("1.000000")
    assert freshness_report.max_contradiction_pressure == d("0.800000")
    assert freshness_report.min_source_agreement_score == d("0.300000")
    assert freshness_report.min_extraction_confidence == d("0.400000")
    assert freshness_report.status == "block"
    assert freshness_report.paper_only is True
    assert freshness_report.report_only is True
    assert freshness_report.readonly is True

    rows = {row.event_claim_bucket: row for row in freshness_report.rows}
    assert tuple(sorted(rows)) == ("official-policy", "regional-board", "thin-feed")

    assert rows["official-policy"].status == "pass"
    assert rows["official-policy"].freshness_ratio == d("0.750000")
    assert rows["official-policy"].stale_source_ratio == d("0.250000")
    assert rows["official-policy"].quorum_gap_count == d("0")
    assert rows["official-policy"].freshness_quorum_score == d("0.000000")
    assert rows["official-policy"].reason_codes == ("event_claim_freshness_quorum_pass",)

    assert rows["regional-board"].status == "watch"
    assert rows["regional-board"].freshness_ratio == d("0.250000")
    assert rows["regional-board"].stale_source_count == d("3")
    assert rows["regional-board"].stale_source_ratio == d("0.750000")
    assert rows["regional-board"].latest_verification_age_seconds == d("10800.000000")
    assert rows["regional-board"].quorum_gap_count == d("1")
    assert rows["regional-board"].primary_quorum_gap_count == d("0")
    assert rows["regional-board"].freshness_quorum_score == d("0.428571")
    assert rows["regional-board"].reason_codes == (
        "fresh_source_quorum_watch",
        "latest_verification_age_watch",
        "stale_source_ratio_watch",
        "source_agreement_watch",
        "contradiction_pressure_watch",
        "extraction_confidence_watch",
    )

    assert rows["thin-feed"].status == "block"
    assert rows["thin-feed"].freshness_ratio == d("0.000000")
    assert rows["thin-feed"].stale_source_count == d("5")
    assert rows["thin-feed"].stale_source_ratio == d("1.000000")
    assert rows["thin-feed"].latest_verification_age_seconds == d("28800.000000")
    assert rows["thin-feed"].quorum_gap_count == d("2")
    assert rows["thin-feed"].primary_quorum_gap_count == d("1")
    assert rows["thin-feed"].freshness_quorum_score == d("1.000000")
    assert rows["thin-feed"].reason_codes == (
        "fresh_source_quorum_block",
        "primary_fresh_source_quorum_block",
        "latest_verification_age_block",
        "stale_source_ratio_block",
        "source_agreement_block",
        "contradiction_pressure_block",
        "extraction_confidence_block",
    )


def test_payload_is_public_safe_deterministic_decimal_only_and_digest_validated() -> None:
    module = api()
    observations = (
        observation(
            event_claim_bucket="regional-board",
            fresh_source_count=d("1"),
            primary_fresh_source_count=d("1"),
        ),
        observation(event_claim_bucket="official-policy"),
    )

    first = report(
        *observations,
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = report(*tuple(reversed(observations)))
    first_payload = module.research_source_event_claim_freshness_quorum_report_payload(first)
    second_payload = module.research_source_event_claim_freshness_quorum_report_payload(second)
    payload_text = repr(first_payload).lower()

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["event_claim_bucket_count"] == "2"
    assert first_payload["rows"][0]["event_claim_bucket"] == "official-policy"
    assert first_payload["rows"][0]["latest_verification_age_seconds"] == "1800.000000"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first.derived_validation_digest == second.derived_validation_digest
    assert_no_float(first_payload)

    for unsafe in (
        "candidate",
        "market",
        "slug",
        "question",
        "http",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert unsafe not in payload_text

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_validates_inputs_statuses_flags_and_frozen_outputs() -> None:
    module = api()
    freshness_report = report(observation())

    assert module.STATUSES == ("pass", "watch", "block")
    with pytest.raises(FrozenInstanceError):
        freshness_report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="latest_verified_at must be a datetime"):
        observation(latest_verified_at=_DatetimeSubclass(2026, 7, 8, 11, tzinfo=UTC))

    with pytest.raises(ValueError, match="latest_verified_at must be timezone-aware"):
        observation(latest_verified_at=datetime(2026, 7, 8, 11, tzinfo=_NoneOffsetTimezone()))

    with pytest.raises(ValueError, match="source_family_count must be a Decimal"):
        observation(source_family_count=1)

    with pytest.raises(ValueError, match="watch_latest_verification_age_seconds must be finite"):
        config(watch_latest_verification_age_seconds=Decimal("NaN"))

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="research-source-event-claim-freshness-quorum-v1")

    for unsafe_bucket in (
        "candidate-alpha",
        "market-alpha",
        "slug-alpha",
        "question-alpha",
        "https-alpha",
        "url-alpha",
        "source-text-alpha",
        "dsn-alpha",
        "table-alpha",
        "token-alpha",
        "wallet-alpha",
        "order-alpha",
        "trade-alpha",
        "live-alpha",
    ):
        with pytest.raises(ValueError, match="event_claim_bucket has unsafe public value"):
            observation(event_claim_bucket=unsafe_bucket)

    with pytest.raises(ValueError, match="config must be readonly"):
        config(readonly=False)

    with pytest.raises(ValueError, match="observation must be paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="status"):
        replace(freshness_report.rows[0], status="blocked")

    with pytest.raises(ValueError, match="event_claim_bucket_count"):
        replace(freshness_report, event_claim_bucket_count=d("2"))


def test_rejects_temporal_inconsistency_empty_inputs_and_bad_quorum_counts() -> None:
    with pytest.raises(ValueError, match="observations must not be empty"):
        report()

    with pytest.raises(ValueError, match="latest_verified_at must not be after generated_at"):
        report(observation(latest_verified_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="fresh_source_count must not exceed source_family_count"):
        observation(source_family_count=d("1"), fresh_source_count=d("2"))

    with pytest.raises(
        ValueError,
        match="primary_fresh_source_count must not exceed fresh_source_count",
    ):
        observation(fresh_source_count=d("1"), primary_fresh_source_count=d("2"))

    freshness_report = report(
        observation(
            event_claim_bucket="missing-check",
            latest_verified_at=None,
            source_family_count=d("2"),
            fresh_source_count=d("0"),
            primary_fresh_source_count=d("0"),
        ),
    )
    row = freshness_report.rows[0]

    assert row.status == "block"
    assert row.latest_verification_age_seconds == d("21600.000000")
    assert "latest_verification_age_block" in row.reason_codes
    assert "fresh_source_quorum_block" in row.reason_codes


def test_module_scope_has_no_forbidden_runtime_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_source_event_claim_freshness_quorum_report.py",
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
        "src/polymarket_alpha_lab/research_source_event_claim_freshness_quorum_report.py",
    ).read_text(encoding="utf-8")

    assert ".timestamp(" not in source
    assert ".total_seconds(" not in source
