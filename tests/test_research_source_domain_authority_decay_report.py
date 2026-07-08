from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_domain_authority_decay_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_domain_authority_decay_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "source-domain-authority-decay-report-v0",
        "fresh_authority_age_seconds": d("3600.000000"),
        "stale_authority_age_seconds": d("86400.000000"),
        "pass_domain_authority_score": d("0.750000"),
        "block_domain_authority_score": d("0.350000"),
        "watch_contradiction_pressure": d("0.250000"),
        "block_contradiction_pressure": d("0.600000"),
        "watch_retrieval_reliability": d("0.700000"),
        "block_retrieval_reliability": d("0.400000"),
        "authority_freshness_weight": d("0.350000"),
        "corroboration_decay_weight": d("0.250000"),
        "retrieval_reliability_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.200000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceDomainAuthorityDecayReportConfig(**values)


def observation(
    source_domain: str = "official-agency",
    *,
    source_family: str = "official-authority",
    observed_at: datetime = OBSERVED_AT,
    authority_score: Decimal = d("0.900000"),
    corroboration_score: Decimal = d("0.800000"),
    contradiction_pressure: Decimal = d("0.100000"),
    retrieval_attempt_count: Decimal = d("10"),
    retrieval_failure_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceDomainAuthorityDecayObservation(
        source_domain=source_domain,
        source_family=source_family,
        observed_at=observed_at,
        authority_score=authority_score,
        corroboration_score=corroboration_score,
        contradiction_pressure=contradiction_pressure,
        retrieval_attempt_count=retrieval_attempt_count,
        retrieval_failure_count=retrieval_failure_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
):
    module = api()
    return module.build_research_source_domain_authority_decay_report(
        observations,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_code_counts", "reason_codes"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "score",
                "pressure",
                "reliability",
                "age",
            )
        ):
            item = getattr(value, field.name)
            if item is not None:
                assert type(item) is Decimal, field.name


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "raw",
        "url",
        "text",
        "candidate_id",
        "market_id",
        "market_slug",
        "condition_id",
        "slug",
        "question",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "network",
        "database",
        "authentication",
        "authorization",
        "private_key",
        "api_key",
        "trade",
        "recommendation",
        "sizing",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate-id",
        "market-id",
        "market_slug",
        "condition-id",
        "question",
        "postgres",
        "database",
        "wallet",
        "order",
        "trade",
        "recommendation",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_empty_input_returns_block_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == "source-domain-authority-decay-report-v0"
    assert empty_report.status == "block"
    assert empty_report.reason_codes == (
        "source_domain_authority_decay_no_inputs",
        "source_domain_authority_decay_report_block",
    )
    assert empty_report.domain_count == d("0")
    assert empty_report.observation_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.average_domain_authority_score is None
    assert empty_report.max_contradiction_pressure == d("0.000000")
    assert empty_report.min_retrieval_reliability_score == d("1.000000")
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_numbers(empty_report)

    payload = module.research_source_domain_authority_decay_report_payload(
        empty_report,
    )
    digest_value = module.research_source_domain_authority_decay_report_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["status"] == "block"
    assert payload["domain_count"] == "0"
    assert payload["min_retrieval_reliability_score"] == "1.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64


def test_report_aggregates_domain_authority_decay_statuses_and_reason_codes() -> None:
    built = report(
        observation(
            "domain-pass",
            source_family="official-a",
            authority_score=d("0.900000"),
            corroboration_score=d("0.800000"),
            contradiction_pressure=d("0.100000"),
            retrieval_attempt_count=d("10"),
            retrieval_failure_count=d("0"),
        ),
        observation(
            "domain-pass",
            source_family="official-b",
            authority_score=d("0.800000"),
            corroboration_score=d("0.700000"),
            contradiction_pressure=d("0.150000"),
            retrieval_attempt_count=d("10"),
            retrieval_failure_count=d("1"),
        ),
        observation(
            "domain-watch",
            source_family="independent-research",
            authority_score=d("0.600000"),
            corroboration_score=d("0.500000"),
            contradiction_pressure=d("0.200000"),
            retrieval_attempt_count=d("5"),
            retrieval_failure_count=d("1"),
        ),
        observation(
            "domain-block",
            source_family="official-stale",
            observed_at=GENERATED_AT - timedelta(seconds=90000),
            authority_score=d("0.900000"),
            corroboration_score=d("0.400000"),
            contradiction_pressure=d("0.800000"),
            retrieval_attempt_count=d("4"),
            retrieval_failure_count=d("3"),
        ),
    )

    assert built.status == "block"
    assert built.domain_count == d("3")
    assert built.observation_count == d("4")
    assert built.pass_count == d("1")
    assert built.watch_count == d("1")
    assert built.block_count == d("1")
    assert built.average_domain_authority_score == d("0.530000")
    assert built.max_contradiction_pressure == d("0.800000")
    assert built.min_retrieval_reliability_score == d("0.250000")
    assert tuple(row.source_domain for row in built.rows) == (
        "domain-block",
        "domain-watch",
        "domain-pass",
    )

    blocked, watched, passed = built.rows
    assert blocked.status == "block"
    assert blocked.observation_count == d("1")
    assert blocked.source_family_count == d("1")
    assert blocked.latest_authority_age_seconds == d("90000.000000")
    assert blocked.average_authority_score == d("0.900000")
    assert blocked.authority_freshness_score == d("0.000000")
    assert blocked.corroboration_decay_score == d("0.000000")
    assert blocked.contradiction_pressure == d("0.800000")
    assert blocked.retrieval_reliability_score == d("0.250000")
    assert blocked.domain_authority_score == d("0.090000")
    assert blocked.reason_codes == (
        "authority_freshness_block",
        "contradiction_pressure_block",
        "corroboration_decay_block",
        "domain_authority_score_block",
        "retrieval_reliability_block",
        "source_domain_authority_decay_block",
    )

    assert watched.status == "watch"
    assert watched.authority_freshness_score == d("0.600000")
    assert watched.corroboration_decay_score == d("0.500000")
    assert watched.contradiction_pressure == d("0.200000")
    assert watched.retrieval_reliability_score == d("0.800000")
    assert watched.domain_authority_score == d("0.655000")
    assert watched.reason_codes == (
        "authority_freshness_watch",
        "corroboration_decay_watch",
        "domain_authority_score_watch",
        "source_domain_authority_decay_watch",
    )

    assert passed.status == "pass"
    assert passed.observation_count == d("2")
    assert passed.source_family_count == d("2")
    assert passed.average_authority_score == d("0.850000")
    assert passed.authority_freshness_score == d("0.850000")
    assert passed.corroboration_decay_score == d("0.750000")
    assert passed.contradiction_pressure == d("0.150000")
    assert passed.retrieval_reliability_score == d("0.950000")
    assert passed.domain_authority_score == d("0.845000")
    assert passed.reason_codes == ("source_domain_authority_decay_passed",)


def test_payload_is_deterministic_public_safe_decimal_string_and_digest_validated() -> None:
    module = api()
    observations = (
        observation(
            "domain-alpha",
            source_family="official-a",
            authority_score=d("0.900000"),
            corroboration_score=d("0.800000"),
        ),
        observation(
            "domain-alpha",
            source_family="archive-a",
            authority_score=d("0.800000"),
            corroboration_score=d("0.700000"),
            retrieval_failure_count=d("1"),
        ),
        observation(
            "domain-beta",
            source_family="official-b",
            authority_score=d("0.600000"),
            corroboration_score=d("0.500000"),
            contradiction_pressure=d("0.700000"),
            retrieval_attempt_count=d("4"),
            retrieval_failure_count=d("2"),
        ),
    )
    first = report(*observations)
    second = report(*reversed(observations))

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["domain_count"] == "2"
    assert payload["rows"][0]["source_domain"] == "domain-beta"
    assert payload["rows"][0]["contradiction_pressure"] == "0.700000"
    assert payload["rows"][1]["source_family_count"] == "2"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_source_domain_authority_decay_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_numbers(first)

    tampered = report(*observations)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_domain_authority_decay_report_payload(tampered)


def test_dataclasses_are_frozen_and_enforce_hard_flags_statuses_types_and_surfaces() -> None:
    module = api()
    built = report(
        observation("domain-alpha", source_family="official-a"),
        observation(
            "domain-alpha",
            source_family="archive-alpha",
            authority_score=d("0.800000"),
            corroboration_score=d("0.700000"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadObservation(module.ResearchSourceDomainAuthorityDecayObservation):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        observation(authority_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly Decimal"):
        observation(authority_score=_DecimalSubclass("0.900000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="retrieval_failure_count"):
        observation(retrieval_attempt_count=d("2"), retrieval_failure_count=d("3"))

    with pytest.raises(ValueError, match="paper_only must be a bool"):
        observation(paper_only=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="unsafe"):
        observation(source_domain="https://example.invalid/source")

    with pytest.raises(ValueError, match="unsafe"):
        observation(source_domain="market-id-123")

    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(contradiction_pressure_weight=d("0.100000"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    public_names = set(module.__all__)
    for fragment in (
        "client",
        "wallet",
        "order",
        "database",
        "network",
        "recommendation",
        "sizing",
        "trade",
    ):
        assert all(fragment not in name.lower() for name in public_names)
