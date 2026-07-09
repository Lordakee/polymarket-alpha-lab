from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_multi_scraper_freshness_consensus_report"
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "research-source-multi-scraper-freshness-consensus-report-v0",
        "watch_fresh_scraper_count": d("2.000000"),
        "block_fresh_scraper_count": d("0.000000"),
        "watch_consensus_scraper_count": d("1.000000"),
        "block_consensus_scraper_count": d("0.000000"),
        "watch_latest_scrape_age_seconds": d("3600.000000"),
        "block_latest_scrape_age_seconds": d("14400.000000"),
        "watch_stale_scraper_ratio": d("0.500000"),
        "block_stale_scraper_ratio": d("0.850000"),
        "watch_consensus_agreement_score": d("0.750000"),
        "block_consensus_agreement_score": d("0.450000"),
        "watch_disagreement_pressure": d("0.250000"),
        "block_disagreement_pressure": d("0.650000"),
        "watch_parse_success_ratio": d("0.850000"),
        "block_parse_success_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourceMultiScraperFreshnessConsensusConfig(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "scraper_bucket": "official-feed",
        "scraper_family_count": d("4.000000"),
        "fresh_scraper_count": d("3.000000"),
        "consensus_scraper_count": d("2.000000"),
        "latest_scraped_at": ago(900),
        "consensus_agreement_score": d("0.920000"),
        "disagreement_pressure": d("0.040000"),
        "parse_success_ratio": d("0.950000"),
    }
    values.update(overrides)
    return module.ResearchSourceMultiScraperFreshnessConsensusObservation(**values)


def build_report(*rows: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_source_multi_scraper_freshness_consensus_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_builds_multi_scraper_freshness_consensus_report_from_public_inputs() -> None:
    module = api()
    report = build_report(
        observation(scraper_bucket="official-feed"),
        observation(
            scraper_bucket="regional-feed",
            fresh_scraper_count=d("1.000000"),
            consensus_scraper_count=d("1.000000"),
            latest_scraped_at=ago(7200),
            consensus_agreement_score=d("0.650000"),
            disagreement_pressure=d("0.350000"),
            parse_success_ratio=d("0.700000"),
        ),
        observation(
            scraper_bucket="thin-feed",
            scraper_family_count=d("5.000000"),
            fresh_scraper_count=d("0.000000"),
            consensus_scraper_count=d("0.000000"),
            latest_scraped_at=ago(28800),
            consensus_agreement_score=d("0.300000"),
            disagreement_pressure=d("0.800000"),
            parse_success_ratio=d("0.400000"),
        ),
    )

    assert type(report) is module.ResearchSourceMultiScraperFreshnessConsensusReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.scraper_bucket_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.min_fresh_scraper_count == d("0.000000")
    assert report.min_consensus_scraper_count == d("0.000000")
    assert report.max_latest_scrape_age_seconds == d("28800.000000")
    assert report.max_stale_scraper_ratio == d("1.000000")
    assert report.max_disagreement_pressure == d("0.800000")
    assert report.min_consensus_agreement_score == d("0.300000")
    assert report.min_parse_success_ratio == d("0.400000")
    assert tuple(row.scraper_bucket for row in report.rows) == (
        "official-feed",
        "regional-feed",
        "thin-feed",
    )

    passed, watched, blocked = report.rows
    assert passed.status == "pass"
    assert passed.fresh_scraper_ratio == d("0.750000")
    assert passed.stale_scraper_ratio == d("0.250000")
    assert passed.freshness_consensus_score == d("0.000000")
    assert passed.reason_codes == ("multi_scraper_freshness_consensus_pass",)

    assert watched.status == "watch"
    assert watched.stale_scraper_count == d("3.000000")
    assert watched.stale_scraper_ratio == d("0.750000")
    assert watched.latest_scrape_age_seconds == d("7200.000000")
    assert watched.fresh_scraper_gap_count == d("1.000000")
    assert watched.consensus_scraper_gap_count == d("0.000000")
    assert watched.freshness_consensus_score == d("0.428571")
    assert watched.reason_codes == (
        "fresh_scraper_quorum_watch",
        "latest_scrape_age_watch",
        "stale_scraper_ratio_watch",
        "consensus_agreement_watch",
        "disagreement_pressure_watch",
        "parse_success_ratio_watch",
    )

    assert blocked.status == "block"
    assert blocked.stale_scraper_count == d("5.000000")
    assert blocked.stale_scraper_ratio == d("1.000000")
    assert blocked.latest_scrape_age_seconds == d("28800.000000")
    assert blocked.fresh_scraper_gap_count == d("2.000000")
    assert blocked.consensus_scraper_gap_count == d("1.000000")
    assert blocked.freshness_consensus_score == d("1.000000")
    assert blocked.reason_codes == (
        "fresh_scraper_quorum_block",
        "consensus_scraper_quorum_block",
        "latest_scrape_age_block",
        "stale_scraper_ratio_block",
        "consensus_agreement_block",
        "disagreement_pressure_block",
        "parse_success_ratio_block",
    )


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    observations = (
        observation(
            scraper_bucket="regional-feed",
            fresh_scraper_count=d("1.000000"),
            consensus_scraper_count=d("1.000000"),
        ),
        observation(scraper_bucket="official-feed"),
    )

    first = build_report(
        *observations,
        generated_at=datetime(2026, 7, 9, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = build_report(*tuple(reversed(observations)))
    first_payload = module.research_source_multi_scraper_freshness_consensus_report_payload(first)
    second_payload = module.research_source_multi_scraper_freshness_consensus_report_payload(second)

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["scraper_bucket_count"] == "2.000000"
    assert first_payload["rows"][0]["scraper_bucket"] == "official-feed"
    assert first_payload["rows"][0]["latest_scrape_age_seconds"] == "900.000000"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first.derived_validation_digest == second.derived_validation_digest
    json.dumps(first_payload, allow_nan=False, sort_keys=True)
    assert_no_public_numeric_values(first_payload)
    assert_payload_has_no_leaked_values(first_payload)
    module.validate_research_source_multi_scraper_freshness_consensus_report_digest(first)
    module.validate_research_source_multi_scraper_freshness_consensus_public_payload(first_payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    tampered = dict(first_payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_multi_scraper_freshness_consensus_public_payload(
            tampered,
        )
    numeric_payload = dict(first_payload)
    numeric_payload["watch_count"] = 1
    numeric_payload["derived_validation_digest"] = canonical_digest(numeric_payload)
    with pytest.raises(ValueError, match="numeric public payload values"):
        module.validate_research_source_multi_scraper_freshness_consensus_public_payload(
            numeric_payload,
        )


def test_public_payload_validation_rejects_resigned_schema_and_semantic_drift() -> None:
    module = api()
    report = build_report(observation())
    payload = module.research_source_multi_scraper_freshness_consensus_report_payload(
        report,
    )

    extra_report_field = json.loads(json.dumps(payload, sort_keys=True))
    extra_report_field["audit_note"] = "safe"
    extra_report_field["derived_validation_digest"] = canonical_digest(
        extra_report_field,
    )
    with pytest.raises(ValueError, match="exact public schema"):
        module.validate_research_source_multi_scraper_freshness_consensus_public_payload(
            extra_report_field,
        )

    missing_report_field = json.loads(json.dumps(payload, sort_keys=True))
    del missing_report_field["max_disagreement_pressure"]
    missing_report_field["derived_validation_digest"] = canonical_digest(
        missing_report_field,
    )
    with pytest.raises(ValueError, match="exact public schema"):
        module.validate_research_source_multi_scraper_freshness_consensus_public_payload(
            missing_report_field,
        )

    extra_row_field = json.loads(json.dumps(payload, sort_keys=True))
    extra_row_field["rows"][0]["audit_note"] = "safe"
    extra_row_field["derived_validation_digest"] = canonical_digest(extra_row_field)
    with pytest.raises(ValueError, match="exact public schema"):
        module.validate_research_source_multi_scraper_freshness_consensus_public_payload(
            extra_row_field,
        )

    unsafe_flags = json.loads(json.dumps(payload, sort_keys=True))
    unsafe_flags["paper_only"] = False
    unsafe_flags["derived_validation_digest"] = canonical_digest(unsafe_flags)
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_research_source_multi_scraper_freshness_consensus_public_payload(
            unsafe_flags,
        )

    noncanonical_decimal = json.loads(json.dumps(payload, sort_keys=True))
    noncanonical_decimal["scraper_bucket_count"] = "1"
    noncanonical_decimal["derived_validation_digest"] = canonical_digest(
        noncanonical_decimal,
    )
    with pytest.raises(ValueError, match="canonical Decimal string"):
        module.validate_research_source_multi_scraper_freshness_consensus_public_payload(
            noncanonical_decimal,
        )

    inconsistent_score = json.loads(json.dumps(payload, sort_keys=True))
    inconsistent_score["rows"][0]["freshness_consensus_score"] = "0.500000"
    inconsistent_score["derived_validation_digest"] = canonical_digest(
        inconsistent_score,
    )
    with pytest.raises(ValueError, match="freshness_consensus_score"):
        module.validate_research_source_multi_scraper_freshness_consensus_public_payload(
            inconsistent_score,
        )


def test_nonnegative_decimals_normalize_negative_zero_for_canonical_digest() -> None:
    module = api()
    positive = build_report(
        observation(
            scraper_bucket="zero-feed",
            fresh_scraper_count=d("0"),
            consensus_scraper_count=d("0"),
            latest_scraped_at=None,
            consensus_agreement_score=d("0"),
            disagreement_pressure=d("0"),
            parse_success_ratio=d("0"),
        ),
    )
    negative = build_report(
        observation(
            scraper_bucket="zero-feed",
            fresh_scraper_count=d("-0"),
            consensus_scraper_count=d("-0"),
            latest_scraped_at=None,
            consensus_agreement_score=d("-0"),
            disagreement_pressure=d("-0"),
            parse_success_ratio=d("-0"),
        ),
    )

    positive_payload = (
        module.research_source_multi_scraper_freshness_consensus_report_payload(
            positive,
        )
    )
    negative_payload = (
        module.research_source_multi_scraper_freshness_consensus_report_payload(
            negative,
        )
    )

    assert negative_payload == positive_payload
    assert negative.derived_validation_digest == positive.derived_validation_digest


def test_report_digest_is_independent_of_ambient_decimal_context() -> None:
    module = api()
    values = (
        observation(
            scraper_bucket="context-feed",
            scraper_family_count=d("7.000000"),
            fresh_scraper_count=d("2.000000"),
            consensus_scraper_count=d("1.000000"),
            latest_scraped_at=ago(3661),
            consensus_agreement_score=d("0.740000"),
            disagreement_pressure=d("0.260000"),
            parse_success_ratio=d("0.840000"),
        ),
    )
    baseline = build_report(*values)

    with localcontext() as ambient:
        ambient.prec = 6
        constrained = build_report(*values)

    baseline_payload = (
        module.research_source_multi_scraper_freshness_consensus_report_payload(
            baseline,
        )
    )
    constrained_payload = (
        module.research_source_multi_scraper_freshness_consensus_report_payload(
            constrained,
        )
    )

    assert constrained_payload == baseline_payload
    assert constrained.derived_validation_digest == baseline.derived_validation_digest


def test_validates_inputs_flags_statuses_frozen_outputs_and_public_shape() -> None:
    module = api()
    report = build_report(observation())
    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "recommendation",
    }
    keys = {
        field.name
        for cls in (type(config()), type(observation()), type(report), type(report.rows[0]))
        for field in fields(cls)
    }

    assert module.RESEARCH_SOURCE_MULTI_SCRAPER_FRESHNESS_CONSENSUS_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert unsafe_keys.isdisjoint(keys)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"

    with pytest.raises(ValueError, match="latest_scraped_at must be a datetime"):
        observation(latest_scraped_at=_DatetimeSubclass(2026, 7, 9, 11, tzinfo=UTC))
    with pytest.raises(ValueError, match="latest_scraped_at must be timezone-aware"):
        observation(latest_scraped_at=datetime(2026, 7, 9, 11, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="scraper_family_count must be a Decimal"):
        observation(scraper_family_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="parse_success_ratio must be a Decimal"):
        observation(parse_success_ratio=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="research-source-multi-scraper-freshness-consensus-report-v1")
    with pytest.raises(ValueError, match="watch_latest_scrape_age_seconds"):
        config(watch_latest_scrape_age_seconds=Decimal("NaN"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="scraper_bucket_count"):
        replace(report, scraper_bucket_count=d("2.000000"))

    for unsafe_bucket in (
        "candidate-alpha",
        "market-alpha",
        "slug-alpha",
        "question-alpha",
        "https-alpha",
        "url-alpha",
        "raw-alpha",
        "source-text-alpha",
        "dsn-alpha",
        "table-alpha",
        "token-alpha",
        "wallet-alpha",
        "order-alpha",
        "trade-alpha",
        "live-alpha",
        "recommendation-alpha",
        "auth-feed",
        "private-key-feed",
        "secret-feed",
        "api-key-feed",
        "credential-feed",
        "password-feed",
        "bearer-feed",
    ):
        with pytest.raises(ValueError, match="scraper_bucket contains unsafe text"):
            observation(scraper_bucket=unsafe_bucket)


def test_rejects_temporal_inconsistency_empty_inputs_and_bad_scraper_counts() -> None:
    with pytest.raises(ValueError, match="observations must not be empty"):
        build_report()

    with pytest.raises(ValueError, match="latest_scraped_at must not be after generated_at"):
        build_report(observation(latest_scraped_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="fresh_scraper_count must not exceed scraper_family_count"):
        observation(scraper_family_count=d("1.000000"), fresh_scraper_count=d("2.000000"))

    with pytest.raises(
        ValueError,
        match="consensus_scraper_count must not exceed fresh_scraper_count",
    ):
        observation(fresh_scraper_count=d("1.000000"), consensus_scraper_count=d("2.000000"))

    report = build_report(
        observation(
            scraper_bucket="missing-feed",
            latest_scraped_at=None,
            scraper_family_count=d("2.000000"),
            fresh_scraper_count=d("0.000000"),
            consensus_scraper_count=d("0.000000"),
        ),
    )
    row = report.rows[0]

    assert row.status == "block"
    assert row.latest_scrape_age_seconds == d("14400.000000")
    assert "latest_scrape_age_block" in row.reason_codes
    assert "fresh_scraper_quorum_block" in row.reason_codes


def test_module_scope_is_pure_report_only_without_external_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_source_multi_scraper_freshness_consensus_report.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Name):
            assert node.id.lower() not in FORBIDDEN_RUNTIME_NAMES
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in FORBIDDEN_RUNTIME_NAMES
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in FORBIDDEN_CALLS
            assert call_name.lower() not in FORBIDDEN_RUNTIME_NAMES

    forbidden_import_fragments = (
        "auth",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert ".timestamp(" not in source
    assert ".total_seconds(" not in source


FORBIDDEN_CALLS = {
    "connect",
    "execute",
    "executemany",
    "open",
    "request",
    "post",
    "put",
    "patch",
    "submit_order",
    "place_order",
    "recommend",
    "size_position",
}
FORBIDDEN_RUNTIME_NAMES = {
    "auth",
    "wallet",
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
    "connect",
    "commit",
    "rollback",
    "cursor",
    "open",
}


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)
    else:
        assert type(value) is not float
        assert type(value) is not int


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
        "recommendation",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
