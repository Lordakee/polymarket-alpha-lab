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


MODULE_NAME = "polymarket_alpha_lab.research_source_claim_update_priority_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_claim_update_priority_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api() -> Any:
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


def cfg(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "research-source-claim-update-priority-report-v0",
        "max_update_age_seconds": d("7200.000000"),
        "component_watch_threshold": d("0.500000"),
        "component_block_threshold": d("0.800000"),
        "priority_watch_threshold": d("0.350000"),
        "priority_block_threshold": d("0.700000"),
        "freshness_weight": d("0.150000"),
        "authority_weight": d("0.200000"),
        "independence_weight": d("0.150000"),
        "contradiction_weight": d("0.200000"),
        "domain_relevance_weight": d("0.150000"),
        "resolution_rule_linkage_weight": d("0.150000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceClaimUpdatePriorityConfig(**values)


def observation(
    update_label: str,
    *,
    source_family_label: str = "official_reporting",
    domain_bucket: str = "macro_policy",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    authority_score: Decimal = d("0.600000"),
    independent_source_count: Decimal = d("1.000000"),
    expected_independent_source_count: Decimal = d("2.000000"),
    contradiction_severity: Decimal = d("0.400000"),
    domain_relevance_score: Decimal = d("0.500000"),
    resolution_rule_linkage_score: Decimal = d("0.600000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceClaimUpdatePriorityObservation(
        update_label=update_label,
        source_family_label=source_family_label,
        domain_bucket=domain_bucket,
        observed_at=observed_at,
        authority_score=authority_score,
        independent_source_count=independent_source_count,
        expected_independent_source_count=expected_independent_source_count,
        contradiction_severity=contradiction_severity,
        domain_relevance_score=domain_relevance_score,
        resolution_rule_linkage_score=resolution_rule_linkage_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def sample_observations() -> tuple[Any, ...]:
    return (
        observation(
            "update-watch",
            source_family_label="specialist_notes",
            domain_bucket="sports_roster",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            authority_score=d("0.600000"),
            independent_source_count=d("1.000000"),
            expected_independent_source_count=d("2.000000"),
            contradiction_severity=d("0.500000"),
            domain_relevance_score=d("0.500000"),
            resolution_rule_linkage_score=d("0.600000"),
        ),
        observation(
            "update-pass",
            source_family_label="social_summary",
            domain_bucket="general_context",
            observed_at=GENERATED_AT - timedelta(minutes=90),
            authority_score=d("0.200000"),
            independent_source_count=d("0.000000"),
            expected_independent_source_count=d("2.000000"),
            contradiction_severity=d("0.050000"),
            domain_relevance_score=d("0.200000"),
            resolution_rule_linkage_score=d("0.100000"),
        ),
        observation(
            "update-block",
            source_family_label="official_reporting",
            domain_bucket="macro_policy",
            observed_at=GENERATED_AT - timedelta(minutes=5),
            authority_score=d("0.950000"),
            independent_source_count=d("3.000000"),
            expected_independent_source_count=d("3.000000"),
            contradiction_severity=d("0.800000"),
            domain_relevance_score=d("0.900000"),
            resolution_rule_linkage_score=d("0.950000"),
        ),
    )


def report(
    observations: tuple[Any, ...] | None = None,
    *,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> Any:
    module = api()
    return module.build_research_source_claim_update_priority_report(
        sample_observations() if observations is None else observations,
        generated_at=generated_at,
        config=config or cfg(),
    )


def assert_no_number_or_datetime_payload_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_number_or_datetime_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_number_or_datetime_payload_values(item)
        return
    assert type(value) not in (Decimal, float, int, datetime)


def assert_no_raw_identifier_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "raw",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "market_id",
        "question",
        "source_text",
        "wallet",
        "order",
        "trade",
        "token",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_raw_identifier_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_raw_identifier_surface(item)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_prioritizes_source_claim_updates_for_analyst_review() -> None:
    built = report()

    assert is_dataclass(built)
    assert built.status == "block"
    assert built.update_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.average_analyst_update_priority_score == d("0.542083")
    assert built.max_analyst_update_priority_score == d("0.921250")
    assert built.max_contradiction_severity == d("0.800000")
    assert built.average_freshness_score == d("0.652778")
    assert built.average_authority_score == d("0.583333")
    assert built.average_independence_score == d("0.500000")
    assert built.average_domain_relevance_score == d("0.533333")
    assert built.average_resolution_rule_linkage_score == d("0.550000")
    assert built.reason_codes == (
        "freshness_watch",
        "freshness_block",
        "authority_watch",
        "authority_block",
        "independence_watch",
        "independence_block",
        "contradiction_watch",
        "contradiction_block",
        "domain_relevance_watch",
        "domain_relevance_block",
        "resolution_rule_linkage_watch",
        "resolution_rule_linkage_block",
        "claim_update_priority_watch",
        "claim_update_priority_block",
        "source_claim_update_priority_pass",
    )

    assert tuple(row.update_label for row in built.rows) == (
        "update-block",
        "update-watch",
        "update-pass",
    )
    assert tuple(row.priority_rank for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.priority_status for row in built.rows) == ("block", "watch", "pass")

    blocked, watched, passed = built.rows
    assert blocked.update_age_seconds == d("300.000000")
    assert blocked.freshness_score == d("0.958333")
    assert blocked.independence_score == d("1.000000")
    assert blocked.analyst_update_priority_score == d("0.921250")
    assert blocked.reason_codes == (
        "freshness_block",
        "authority_block",
        "independence_block",
        "contradiction_block",
        "domain_relevance_block",
        "resolution_rule_linkage_block",
        "claim_update_priority_block",
    )
    assert watched.freshness_score == d("0.750000")
    assert watched.independence_score == d("0.500000")
    assert watched.analyst_update_priority_score == d("0.572500")
    assert watched.reason_codes == (
        "freshness_watch",
        "authority_watch",
        "independence_watch",
        "contradiction_watch",
        "domain_relevance_watch",
        "resolution_rule_linkage_watch",
        "claim_update_priority_watch",
    )
    assert passed.analyst_update_priority_score == d("0.132500")
    assert passed.reason_codes == ("source_claim_update_priority_pass",)


def test_payload_is_deterministic_public_safe_json_ready_and_digest_validated() -> None:
    module = api()
    first = report()
    second = report(tuple(reversed(sample_observations())))

    payload = module.research_source_claim_update_priority_report_payload(first)
    reversed_payload = module.research_source_claim_update_priority_report_payload(second)

    assert payload == reversed_payload
    assert json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["config_version"] == "research-source-claim-update-priority-report-v0"
    assert payload["status"] == "block"
    assert payload["rows"][0]["priority_rank"] == "1.000000"
    assert payload["rows"][0]["analyst_update_priority_score"] == "0.921250"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.research_source_claim_update_priority_report_digest(first) == (
        first.derived_validation_digest
    )
    assert module.validate_research_source_claim_update_priority_public_payload(payload)
    assert_no_number_or_datetime_payload_values(payload)
    assert_no_raw_identifier_surface(payload)
    assert module.research_source_claim_update_priority_report_payload(payload) == payload

    tampered = dict(payload)
    tampered["average_analyst_update_priority_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_claim_update_priority_report_payload(tampered)
    assert not module.validate_research_source_claim_update_priority_public_payload(tampered)

    unsafe = dict(payload)
    unsafe["wallet_surface"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_claim_update_priority_report_payload(unsafe)


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    built = report()

    public_classes = (
        module.ResearchSourceClaimUpdatePriorityConfig,
        module.ResearchSourceClaimUpdatePriorityObservation,
        module.ResearchSourceClaimUpdatePriorityRow,
        module.ResearchSourceClaimUpdatePriorityReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True

    for instance in (cfg(), sample_observations()[0], built, *built.rows):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)

    with pytest.raises(FrozenInstanceError):
        built.rows[0].priority_status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourceClaimUpdatePriorityReport):
            pass

    with pytest.raises(ValueError, match="authority_score must be exactly Decimal"):
        observation("update-float", authority_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independent_source_count must be exactly Decimal"):
        observation(
            "update-decimal-subclass",
            independent_source_count=_DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="whole"):
        observation("update-fractional", independent_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="expected_independent_source_count"):
        observation(
            "update-overcount",
            independent_source_count=d("3.000000"),
            expected_independent_source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample_observations()[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(freshness_weight=d("0.100000"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        observation("update-naive", observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="utcoffset"):
        observation(
            "update-offset",
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report((observation("update-future", observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="unsafe"):
        observation("https://example.invalid/raw-market")


def test_empty_report_is_pass_and_public_exports_have_no_live_surfaces() -> None:
    module = api()
    empty = report(())

    assert module.PRIORITY_STATUSES == ("pass", "watch", "block")
    assert empty.status == "pass"
    assert empty.update_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.block_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("source_claim_update_priority_pass",)
    assert module.validate_research_source_claim_update_priority_public_payload(empty.payload)

    unsafe_public_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source_text",
        "raw_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
    )
    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert not any(term in lowered_name for term in unsafe_public_terms)

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
        "scrapling",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    public_names = set(dir(module))
    assert "client" not in public_names
    assert "wallet" not in public_names
    assert "order" not in public_names
    assert "trade" not in public_names
