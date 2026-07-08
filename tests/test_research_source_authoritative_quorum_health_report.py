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


MODULE_NAME = "polymarket_alpha_lab.research_source_authoritative_quorum_health_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_authoritative_quorum_health_report.py"
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
        "config_version": "source-authoritative-quorum-health-report-v0",
        "min_official_source_count": d("2"),
        "min_independent_corroboration_count": d("2"),
        "max_authority_age_seconds": d("7200.000000"),
        "watch_stale_authority_pressure": d("0.250000"),
        "block_stale_authority_pressure": d("0.600000"),
        "watch_contradiction_exposure": d("0.250000"),
        "block_contradiction_exposure": d("0.600000"),
        "watch_manual_review_urgency": d("0.350000"),
        "block_manual_review_urgency": d("0.700000"),
        "official_quorum_gap_weight": d("0.250000"),
        "independent_corroboration_gap_weight": d("0.250000"),
        "stale_authority_pressure_weight": d("0.250000"),
        "contradiction_exposure_weight": d("0.250000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceAuthoritativeQuorumHealthReportConfig(**values)


def observation(
    scope_id: str = "scope-alpha",
    *,
    source_family: str = "official-agency",
    source_role: str = "official_authority",
    observed_at: datetime = OBSERVED_AT,
    contradiction_exposure: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceAuthoritativeQuorumObservation(
        quorum_scope_id=scope_id,
        source_family=source_family,
        source_role=source_role,
        observed_at=observed_at,
        contradiction_exposure=contradiction_exposure,
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
    return module.build_research_source_authoritative_quorum_health_report(
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
                "pressure",
                "exposure",
                "urgency",
                "age",
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
        "market_id",
        "market_slug",
        "condition_id",
        "question",
        "wallet",
        "order",
        "network",
        "database",
        "authentication",
        "authorization",
        "auth_token",
        "private_key",
        "api_key",
        "recommendation",
        "sizing",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "market-id",
        "market_slug",
        "condition-id",
        "wallet",
        "order",
        "database",
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


def test_empty_input_returns_blocked_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == "source-authoritative-quorum-health-report-v0"
    assert empty_report.status == "block"
    assert empty_report.reason_codes == (
        "authoritative_quorum_health_no_inputs",
        "authoritative_quorum_health_block",
    )
    assert empty_report.scope_count == d("0")
    assert empty_report.official_source_count == d("0")
    assert empty_report.independent_corroboration_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.max_stale_authority_pressure == d("0.000000")
    assert empty_report.max_contradiction_exposure == d("0.000000")
    assert empty_report.max_manual_review_urgency == d("1.000000")
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_numbers(empty_report)

    payload = module.research_source_authoritative_quorum_health_report_payload(
        empty_report,
    )
    digest_value = module.research_source_authoritative_quorum_health_report_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["status"] == "block"
    assert payload["scope_count"] == "0"
    assert payload["max_manual_review_urgency"] == "1.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64


def test_report_aggregates_quorum_health_statuses_and_reason_codes() -> None:
    health = report(
        observation(
            "scope-pass",
            source_family="official-agency-a",
            source_role="official_authority",
            contradiction_exposure=d("0.050000"),
        ),
        observation(
            "scope-pass",
            source_family="official-agency-b",
            source_role="official_authority",
            contradiction_exposure=d("0.100000"),
        ),
        observation(
            "scope-pass",
            source_family="archive-alpha",
            source_role="independent_corroborator",
            contradiction_exposure=d("0.050000"),
        ),
        observation(
            "scope-pass",
            source_family="research-desk-alpha",
            source_role="independent_corroborator",
            contradiction_exposure=d("0.080000"),
        ),
        observation(
            "scope-watch",
            source_family="official-agency-a",
            source_role="official_authority",
            contradiction_exposure=d("0.200000"),
        ),
        observation(
            "scope-watch",
            source_family="official-agency-b",
            source_role="official_authority",
            contradiction_exposure=d("0.180000"),
        ),
        observation(
            "scope-watch",
            source_family="archive-alpha",
            source_role="independent_corroborator",
            contradiction_exposure=d("0.150000"),
        ),
        observation(
            "scope-block",
            source_family="official-agency-a",
            source_role="official_authority",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            contradiction_exposure=d("0.900000"),
        ),
    )

    assert health.status == "block"
    assert health.scope_count == d("3")
    assert health.official_source_count == d("5")
    assert health.independent_corroboration_count == d("3")
    assert health.pass_count == d("1")
    assert health.watch_count == d("1")
    assert health.block_count == d("1")
    assert health.max_stale_authority_pressure == d("1.000000")
    assert health.max_contradiction_exposure == d("0.900000")
    assert health.max_manual_review_urgency == d("0.850000")
    assert tuple(row.quorum_scope_id for row in health.rows) == (
        "scope-block",
        "scope-watch",
        "scope-pass",
    )

    blocked, watched, passed = health.rows
    assert blocked.status == "block"
    assert blocked.official_source_count == d("1")
    assert blocked.independent_corroboration_count == d("0")
    assert blocked.stale_authority_count == d("1")
    assert blocked.max_authority_age_seconds == d("9000.000000")
    assert blocked.stale_authority_pressure == d("1.000000")
    assert blocked.contradiction_exposure == d("0.900000")
    assert blocked.manual_review_urgency == d("0.850000")
    assert blocked.reason_codes == (
        "contradiction_exposure_block",
        "independent_corroboration_gap_block",
        "manual_review_urgency_block",
        "official_quorum_gap_watch",
        "stale_authority_pressure_block",
        "authoritative_quorum_health_block",
    )

    assert watched.status == "watch"
    assert watched.official_source_count == d("2")
    assert watched.independent_corroboration_count == d("1")
    assert watched.stale_authority_count == d("0")
    assert watched.stale_authority_pressure == d("0.000000")
    assert watched.contradiction_exposure == d("0.200000")
    assert watched.manual_review_urgency == d("0.175000")
    assert watched.reason_codes == (
        "independent_corroboration_gap_watch",
        "authoritative_quorum_health_watch",
    )

    assert passed.status == "pass"
    assert passed.official_source_count == d("2")
    assert passed.independent_corroboration_count == d("2")
    assert passed.stale_authority_count == d("0")
    assert passed.max_authority_age_seconds == d("1800.000000")
    assert passed.contradiction_exposure == d("0.100000")
    assert passed.manual_review_urgency == d("0.025000")
    assert passed.reason_codes == ("authoritative_quorum_health_passed",)


def test_payload_is_deterministic_public_safe_decimal_string_and_digest_validated() -> None:
    module = api()
    observations = (
        observation("scope-alpha", source_family="official-a", source_role="official_authority"),
        observation("scope-alpha", source_family="official-b", source_role="official_authority"),
        observation(
            "scope-alpha",
            source_family="archive-alpha",
            source_role="independent_corroborator",
        ),
        observation(
            "scope-alpha",
            source_family="research-desk",
            source_role="independent_corroborator",
        ),
        observation(
            "scope-beta",
            source_family="official-a",
            source_role="official_authority",
            contradiction_exposure=d("0.700000"),
        ),
    )
    first = report(*observations)
    second = report(*reversed(observations))

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["scope_count"] == "2"
    assert payload["rows"][0]["quorum_scope_id"] == "scope-beta"
    assert payload["rows"][0]["official_source_count"] == "1"
    assert payload["rows"][0]["contradiction_exposure"] == "0.700000"
    assert payload["rows"][1]["independent_corroboration_count"] == "2"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_source_authoritative_quorum_health_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_numbers(first)

    tampered = report(*observations)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_authoritative_quorum_health_report_payload(tampered)


def test_dataclasses_are_frozen_and_enforce_hard_flags_statuses_and_types() -> None:
    module = api()
    built = report(
        observation("scope-alpha", source_family="official-a", source_role="official_authority"),
        observation("scope-alpha", source_family="official-b", source_role="official_authority"),
        observation(
            "scope-alpha",
            source_family="archive-alpha",
            source_role="independent_corroborator",
        ),
        observation(
            "scope-alpha",
            source_family="research-desk",
            source_role="independent_corroborator",
        ),
    )

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadObservation(module.ResearchSourceAuthoritativeQuorumObservation):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="clear")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="contradiction_exposure must be a Decimal"):
        observation(contradiction_exposure=0.1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly Decimal"):
        observation(contradiction_exposure=_DecimalSubclass("0.100000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only must be a bool"):
        observation(paper_only=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="unsafe"):
        observation(source_family="https://example.invalid/source")

    with pytest.raises(ValueError, match="unsafe"):
        observation(scope_id="market-id-123")

    with pytest.raises(ValueError, match="source_role"):
        observation(source_role="blog")

    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(contradiction_exposure_weight=d("0.200000"))

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
    ):
        assert all(fragment not in name.lower() for name in public_names)
