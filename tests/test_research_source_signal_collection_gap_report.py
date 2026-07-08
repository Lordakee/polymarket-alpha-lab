from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_signal_collection_gap_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_signal_collection_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "source-signal-collection-gap-report-v0",
        "required_domain_keys": ("authority", "event", "resolution"),
        "min_authoritative_signal_count": d("1"),
        "min_authority_score": d("0.700000"),
        "max_fresh_signal_age_seconds": d("7200.000000"),
        "min_independent_family_count": d("2"),
        "min_corroborating_signal_count": d("2"),
        "watch_collection_gap_score": d("0.350000"),
        "block_collection_gap_score": d("0.700000"),
        "watch_contradiction_exposure": d("0.350000"),
        "block_contradiction_exposure": d("0.700000"),
        "authority_gap_weight": d("0.200000"),
        "freshness_gap_weight": d("0.200000"),
        "independence_gap_weight": d("0.200000"),
        "corroboration_gap_weight": d("0.150000"),
        "contradiction_exposure_weight": d("0.150000"),
        "domain_coverage_gap_weight": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceSignalCollectionGapReportConfig(**values)


def signal(
    scope_id: str = "scope-pass",
    *,
    authority_tier: str = "official_authority",
    family_key: str = "family-official",
    domain_key: str = "authority",
    observed_at: datetime = OBSERVED_AT,
    authority_score: Decimal = d("0.900000"),
    corroborates_scope: bool = True,
    contradiction_exposure: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceSignalCollectionObservation(
        collection_scope_id=scope_id,
        authority_tier=authority_tier,
        family_key=family_key,
        domain_key=domain_key,
        observed_at=observed_at,
        authority_score=authority_score,
        corroborates_scope=corroborates_scope,
        contradiction_exposure=contradiction_exposure,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *signals: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> Any:
    module = api()
    return module.build_research_source_signal_collection_gap_report(
        signals,
        config=config or cfg(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_code_counts"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "score",
                "ratio",
                "exposure",
                "seconds",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


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
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "dsn",
        "table",
        "wallet",
        "order",
        "token",
        "auth_token",
        "authentication",
        "authorization",
        "secret",
        "private_key",
        "api_key",
        "trade",
        "trading",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate",
        "market_slug",
        "slug",
        "dsn",
        "table",
        "wallet",
        "order",
        "token",
        "auth_token",
        "authentication",
        "authorization",
        "secret",
        "private_key",
        "api_key",
        "trade",
        "trading",
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


def test_empty_input_returns_pass_report_only_digest_report() -> None:
    module = api()
    empty_report = report()

    assert type(empty_report) is module.ResearchSourceSignalCollectionGapReport
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == "source-signal-collection-gap-report-v0"
    assert empty_report.status == "pass"
    assert empty_report.reason_codes == ("source_signal_collection_gap_passed",)
    assert empty_report.scope_count == d("0")
    assert empty_report.signal_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.max_collection_gap_score == d("0.000000")
    assert empty_report.average_collection_gap_score == d("0.000000")
    assert empty_report.max_contradiction_exposure == d("0.000000")
    assert empty_report.min_domain_coverage_ratio == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.reason_code_counts == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_numbers(empty_report)

    payload = module.research_source_signal_collection_gap_report_payload(empty_report)
    digest_value = module.research_source_signal_collection_gap_report_digest(empty_report)
    json.dumps(payload, sort_keys=True)
    assert payload["derived_validation_digest"] == digest_value
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)


def test_report_scores_authority_freshness_independence_corroboration_contradiction_and_domain_gaps() -> None:
    built = report(
        signal(
            "scope-pass",
            family_key="family-official",
            domain_key="authority",
            authority_score=d("0.950000"),
            contradiction_exposure=d("0.050000"),
        ),
        signal(
            "scope-pass",
            authority_tier="domain_specialist",
            family_key="family-specialist",
            domain_key="event",
            authority_score=d("0.850000"),
            contradiction_exposure=d("0.100000"),
        ),
        signal(
            "scope-pass",
            authority_tier="independent_archive",
            family_key="family-archive",
            domain_key="resolution",
            authority_score=d("0.800000"),
            contradiction_exposure=d("0.080000"),
        ),
        signal(
            "scope-watch",
            family_key="family-official",
            domain_key="authority",
            authority_score=d("0.900000"),
            corroborates_scope=True,
            contradiction_exposure=d("0.200000"),
        ),
        signal(
            "scope-watch",
            authority_tier="secondary_context",
            family_key="family-news",
            domain_key="event",
            authority_score=d("0.600000"),
            corroborates_scope=False,
            contradiction_exposure=d("0.150000"),
        ),
        signal(
            "scope-block",
            authority_tier="secondary_context",
            family_key="family-secondary",
            domain_key="authority",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            authority_score=d("0.400000"),
            corroborates_scope=False,
            contradiction_exposure=d("0.900000"),
        ),
    )

    assert built.status == "block"
    assert built.scope_count == d("3")
    assert built.signal_count == d("6")
    assert built.pass_count == d("1")
    assert built.watch_count == d("1")
    assert built.block_count == d("1")
    assert built.max_collection_gap_score == d("0.851667")
    assert built.average_collection_gap_score == d("0.335000")
    assert built.max_contradiction_exposure == d("0.900000")
    assert built.min_domain_coverage_ratio == d("0.333333")
    assert tuple(row.collection_scope_id for row in built.rows) == (
        "scope-block",
        "scope-watch",
        "scope-pass",
    )

    blocked, watched, passed = built.rows
    assert blocked.status == "block"
    assert blocked.signal_count == d("1")
    assert blocked.authoritative_signal_count == d("0")
    assert blocked.fresh_signal_count == d("0")
    assert blocked.independent_family_count == d("1")
    assert blocked.corroborating_signal_count == d("0")
    assert blocked.covered_domain_count == d("1")
    assert blocked.authority_gap_ratio == d("1.000000")
    assert blocked.freshness_gap_ratio == d("1.000000")
    assert blocked.independence_gap_ratio == d("0.500000")
    assert blocked.corroboration_gap_ratio == d("1.000000")
    assert blocked.contradiction_exposure == d("0.900000")
    assert blocked.domain_coverage_ratio == d("0.333333")
    assert blocked.domain_coverage_gap_ratio == d("0.666667")
    assert blocked.collection_gap_score == d("0.851667")
    assert blocked.max_signal_age_seconds == d("9000.000000")
    assert blocked.reason_codes == (
        "source_signal_collection_authority_gap_block",
        "source_signal_collection_freshness_gap_block",
        "source_signal_collection_independence_gap_watch",
        "source_signal_collection_corroboration_gap_block",
        "source_signal_collection_contradiction_exposure_block",
        "source_signal_collection_domain_coverage_gap_watch",
        "source_signal_collection_gap_block",
    )

    assert watched.status == "watch"
    assert watched.authoritative_signal_count == d("1")
    assert watched.fresh_signal_count == d("2")
    assert watched.independent_family_count == d("2")
    assert watched.corroborating_signal_count == d("1")
    assert watched.domain_coverage_ratio == d("0.666667")
    assert watched.collection_gap_score == d("0.138333")
    assert watched.reason_codes == (
        "source_signal_collection_corroboration_gap_watch",
        "source_signal_collection_domain_coverage_gap_watch",
        "source_signal_collection_gap_watch",
    )

    assert passed.status == "pass"
    assert passed.collection_gap_score == d("0.015000")
    assert passed.reason_codes == ("source_signal_collection_gap_passed",)


def test_payload_is_deterministic_decimal_string_safe_and_digest_validated() -> None:
    module = api()
    signals = (
        signal("scope-alpha", family_key="family-a", domain_key="authority"),
        signal(
            "scope-alpha",
            authority_tier="domain_specialist",
            family_key="family-b",
            domain_key="event",
            authority_score=d("0.800000"),
        ),
        signal(
            "scope-alpha",
            authority_tier="independent_archive",
            family_key="family-c",
            domain_key="resolution",
            authority_score=d("0.850000"),
        ),
        signal(
            "scope-beta",
            authority_tier="secondary_context",
            family_key="family-d",
            domain_key="authority",
            authority_score=d("0.300000"),
            corroborates_scope=False,
            contradiction_exposure=d("0.800000"),
        ),
    )
    first = report(*signals)
    second = report(*reversed(signals))

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["scope_count"] == "2"
    assert payload["rows"][0]["collection_scope_id"] == "scope-beta"
    assert payload["rows"][0]["authority_gap_ratio"] == "1.000000"
    assert payload["rows"][0]["contradiction_exposure"] == "0.800000"
    assert payload["rows"][1]["collection_gap_score"] == "0.015000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_source_signal_collection_gap_report_digest(first) == (
        first.derived_validation_digest
    )
    assert module.validate_research_source_signal_collection_gap_public_payload(payload)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_numbers(first)

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_signal_collection_gap_public_payload(tampered)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_dataclasses_are_frozen_and_enforce_hard_flags_and_exact_types() -> None:
    module = api()
    built = report(signal(), signal(family_key="family-b", domain_key="event"))

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchSourceSignalCollectionGapReportConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        signal(authority_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="contradiction_exposure must be exactly Decimal"):
        signal(contradiction_exposure=_DecimalSubclass("0.100000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="corroborates_scope must be a bool"):
        signal(corroborates_scope=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        signal(observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))


def test_unsafe_identifiers_and_live_surface_imports_are_rejected() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        signal("candidate_id_123")

    with pytest.raises(ValueError, match="unsafe"):
        signal("market_slug_alpha")

    with pytest.raises(ValueError, match="unsafe"):
        signal(domain_key="https://example.invalid/source")

    with pytest.raises(ValueError, match="unsafe"):
        signal(family_key="postgres_dsn_alias")

    with pytest.raises(ValueError, match="unsafe"):
        signal(authority_tier="orders_table")

    with pytest.raises(ValueError, match="required_domain_keys must be non-empty"):
        cfg(required_domain_keys=())

    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(domain_coverage_gap_weight=d("0.050000"))

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
    public_names = set(dir(api()))
    assert "client" not in public_names
    assert "wallet" not in public_names
    assert "order" not in public_names
    assert "trade" not in public_names
