from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from types import MappingProxyType
from typing import Any

import pytest

import polymarket_alpha_lab.category_playbook_category_threshold_domain_policy_readiness as module

from polymarket_alpha_lab.category_playbook_category_threshold_domain_policy_readiness import (
    CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_STATUSES,
    DEFAULT_CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_VERSION,
    SUPPORTED_CATEGORY_IDS,
    CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig,
    CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput,
    CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport,
    build_category_playbook_category_threshold_domain_policy_readiness_report,
    category_playbook_category_threshold_domain_policy_readiness_config,
    category_playbook_category_threshold_domain_policy_readiness_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _TupleSubclass(tuple):
    pass


def payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(payload_values(item))
        return tuple(values)
    return (value,)


def readiness_input(
    category_id: str = "bitcoin",
    **overrides: Any,
) -> CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput:
    cfg = category_playbook_category_threshold_domain_policy_readiness_config(category_id)
    values: dict[str, Any] = {
        "category_id": category_id,
        "observed_liquidity_usd": cfg.min_liquidity_usd + d("1000.000000"),
        "observed_spread_probability": cfg.max_spread_probability,
        "evidence_source_count": cfg.evidence_quorum,
        "evidence_age_hours": cfg.freshness_sla_hours,
        "playbook_exists": True,
        "playbook_settled_example_count": cfg.playbook_min_settled_examples,
        "playbook_source_family_count": cfg.playbook_min_source_families,
        "manual_review_completed": not cfg.manual_review_required,
    }
    values.update(overrides)
    return CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput(**values)


def report(
    category_id: str = "bitcoin",
    **overrides: Any,
) -> CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport:
    return build_category_playbook_category_threshold_domain_policy_readiness_report(
        readiness_input(category_id, **overrides),
    )


def test_default_configs_cover_required_categories_with_phase1_readonly_thresholds() -> None:
    assert DEFAULT_CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_VERSION == (
        "category-playbook-category-threshold-domain-policy-readiness-v0"
    )
    assert CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_STATUSES == (
        "ready",
        "watch",
        "blocked",
    )
    assert SUPPORTED_CATEGORY_IDS == (
        "politics",
        "macro",
        "bitcoin",
        "equity_index",
        "gold",
        "soccer",
        "basketball",
    )

    configs = {
        category_id: category_playbook_category_threshold_domain_policy_readiness_config(
            category_id,
        )
        for category_id in SUPPORTED_CATEGORY_IDS
    }

    assert configs["politics"].manual_review_required is True
    assert configs["macro"].manual_review_required is True
    assert configs["bitcoin"].manual_review_required is False
    assert configs["equity_index"].manual_review_required is False
    assert configs["gold"].manual_review_required is False
    assert configs["soccer"].manual_review_required is False
    assert configs["basketball"].manual_review_required is False

    for category_id, cfg in configs.items():
        assert type(cfg) is CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig
        assert is_dataclass(cfg)
        assert cfg.category_id == category_id
        assert cfg.domain_policy_id == f"domain-policy-{category_id}-readonly"
        assert cfg.playbook_id == f"category-playbook-{category_id}-readonly"
        assert cfg.min_liquidity_usd > d("0.000000")
        assert d("0.000000") < cfg.max_spread_probability <= d("0.050000")
        assert cfg.evidence_quorum >= d("2")
        assert cfg.freshness_sla_hours > d("0.000000")
        assert cfg.playbook_min_settled_examples >= d("3")
        assert cfg.playbook_min_source_families >= d("2")
        assert cfg.paper_only is True
        assert cfg.report_only is True
        assert cfg.readonly is True
        for item in fields(cfg):
            value = getattr(cfg, item.name)
            if item.name in {
                "category_id",
                "domain_policy_id",
                "playbook_id",
                "manual_review_required",
                "paper_only",
                "report_only",
                "readonly",
            }:
                continue
            assert type(value) is Decimal


def test_report_scores_ready_watch_and_blocked_against_category_policy() -> None:
    ready = report("bitcoin")

    assert ready.readiness_status == "ready"
    assert ready.reason_codes == (
        "domain_policy_readonly",
        "category_thresholds_ready",
        "evidence_quorum_ready",
        "freshness_sla_ready",
        "category_playbook_ready",
        "manual_review_not_required",
        "category_readiness_ready",
    )
    assert ready.manual_next_step == "reuse_category_playbook_for_paper_research"

    watched = report("politics")

    assert watched.readiness_status == "watch"
    assert watched.manual_review_required is True
    assert watched.manual_review_completed is False
    assert watched.reason_codes[-2:] == (
        "manual_review_required",
        "category_readiness_watch",
    )
    assert watched.manual_next_step == "complete_manual_review_before_paper_research"

    blocked = report(
        "basketball",
        observed_liquidity_usd=d("100.000000"),
        observed_spread_probability=d("0.100000"),
        evidence_source_count=d("1"),
        evidence_age_hours=d("48.000000"),
        playbook_exists=False,
        playbook_settled_example_count=d("0"),
        playbook_source_family_count=d("0"),
    )

    assert blocked.readiness_status == "blocked"
    assert blocked.reason_codes == (
        "domain_policy_readonly",
        "min_liquidity_below_category_threshold",
        "max_spread_above_category_threshold",
        "evidence_quorum_missing",
        "freshness_sla_stale",
        "category_playbook_missing",
        "playbook_settled_examples_missing",
        "playbook_source_families_missing",
        "manual_review_not_required",
        "category_readiness_blocked",
    )
    assert blocked.manual_next_step == "repair_category_thresholds_and_playbook_before_reuse"


def test_completed_required_manual_review_is_reported_as_completed() -> None:
    completed = report("politics", manual_review_completed=True)

    assert completed.manual_review_required is True
    assert completed.manual_review_completed is True
    assert completed.readiness_status == "ready"
    assert "manual_review_completed" in completed.reason_codes
    assert "manual_review_not_required" not in completed.reason_codes
    assert "manual_review_required" not in completed.reason_codes


def test_payload_is_json_ready_digest_backed_and_phase1_readonly() -> None:
    summary = report("gold")

    payload = summary.public_payload
    assert payload == category_playbook_category_threshold_domain_policy_readiness_payload(
        summary,
    )
    assert category_playbook_category_threshold_domain_policy_readiness_payload(
        payload,
    ) == payload
    assert payload["category_id"] == "gold"
    assert payload["domain_policy_id"] == "domain-policy-gold-readonly"
    assert payload["playbook_id"] == "category-playbook-gold-readonly"
    assert payload["min_liquidity_usd"] == "10000.000000"
    assert payload["max_spread_probability"] == "0.020000"
    assert payload["evidence_quorum"] == "3"
    assert payload["freshness_sla_hours"] == "2.000000"
    assert payload["readiness_status"] == "ready"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["payload_digest"]) == 64
    assert not any(type(value) in (int, float, Decimal) for value in payload_values(payload))

    tampered_payload = dict(payload)
    tampered_payload["readiness_status"] = "blocked"
    with pytest.raises(ValueError, match="payload_digest"):
        category_playbook_category_threshold_domain_policy_readiness_payload(
            tampered_payload,
        )


def test_report_serializer_rejects_stored_digest_and_content_forgery() -> None:
    digest_tampered = report("gold")
    object.__setattr__(digest_tampered, "payload_digest", "0" * 64)
    with pytest.raises(ValueError, match="payload_digest must match public payload"):
        category_playbook_category_threshold_domain_policy_readiness_payload(
            digest_tampered,
        )

    content_tampered = report("gold")
    object.__setattr__(
        content_tampered,
        "observed_liquidity_usd",
        content_tampered.observed_liquidity_usd + d("1.000000"),
    )
    with pytest.raises(ValueError, match="payload_digest must match public payload"):
        category_playbook_category_threshold_domain_policy_readiness_payload(
            content_tampered,
        )

    pristine = report("gold")
    with pytest.raises(ValueError, match="payload_digest"):
        forged = replace(
            pristine,
            observed_liquidity_usd=(
                pristine.observed_liquidity_usd + d("1.000000")
            ),
            payload_digest="",
        )
        category_playbook_category_threshold_domain_policy_readiness_payload(forged)


def test_payload_rejects_rehashed_noncanonical_category_policy_promotion() -> None:
    blocked = report(
        "gold",
        observed_liquidity_usd=d("9000.000000"),
    )
    forged = dict(blocked.public_payload)
    forged.update(
        min_liquidity_usd="8000.000000",
        readiness_status="ready",
        reason_codes=[
            "domain_policy_readonly",
            "category_thresholds_ready",
            "evidence_quorum_ready",
            "freshness_sla_ready",
            "category_playbook_ready",
            "manual_review_not_required",
            "category_readiness_ready",
        ],
        manual_next_step="reuse_category_playbook_for_paper_research",
    )
    forged["payload_digest"] = module._payload_digest(forged)

    with pytest.raises(ValueError, match="canonical category policy"):
        category_playbook_category_threshold_domain_policy_readiness_payload(forged)


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("min_liquidity_usd", "9000.000000"),
        ("max_spread_probability", "0.030000"),
        ("evidence_quorum", "2"),
        ("freshness_sla_hours", "3.000000"),
        ("playbook_min_settled_examples", "3"),
        ("playbook_min_source_families", "2"),
        ("manual_review_required", True),
    ),
)
def test_payload_rejects_every_rehashed_noncanonical_category_policy_field(
    field_name: str,
    forged_value: object,
) -> None:
    forged = dict(report("gold", manual_review_completed=True).public_payload)
    forged[field_name] = forged_value
    if field_name == "manual_review_required":
        forged["reason_codes"] = [
            (
                "manual_review_completed"
                if reason_code == "manual_review_not_required"
                else reason_code
            )
            for reason_code in forged["reason_codes"]
        ]
    forged["payload_digest"] = module._payload_digest(forged)

    with pytest.raises(ValueError, match="canonical category policy"):
        category_playbook_category_threshold_domain_policy_readiness_payload(forged)


def test_report_serializer_rejects_non_exact_reason_code_container() -> None:
    summary = report("gold")
    object.__setattr__(summary, "reason_codes", _TupleSubclass(summary.reason_codes))

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        category_playbook_category_threshold_domain_policy_readiness_payload(summary)


def test_payload_serializer_materializes_public_mappings_canonically() -> None:
    payload = report("gold").public_payload

    materialized = category_playbook_category_threshold_domain_policy_readiness_payload(
        MappingProxyType(payload),
    )

    assert type(materialized) is dict
    assert materialized == payload
    assert materialized is not payload
    assert type(materialized["reason_codes"]) is list
    assert materialized["reason_codes"] is not payload["reason_codes"]


def test_payload_serializer_rejects_non_exact_string_mapping_keys() -> None:
    payload = report("gold").public_payload
    category_id = payload.pop("category_id")
    payload[_StringSubclass("category_id")] = category_id

    with pytest.raises(ValueError, match="keys must be exact strings"):
        category_playbook_category_threshold_domain_policy_readiness_payload(payload)


def test_validation_rejects_bad_types_unknown_categories_flags_and_subclasses() -> None:
    with pytest.raises(ValueError, match="category_id"):
        category_playbook_category_threshold_domain_policy_readiness_config("tennis")
    with pytest.raises(ValueError, match="observed_liquidity_usd"):
        readiness_input(observed_liquidity_usd=10000)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_spread_probability"):
        readiness_input(observed_spread_probability=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="manual_review_completed"):
        readiness_input(manual_review_completed="yes")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="readonly"):
        readiness_input(readonly=False)

    summary = report()
    with pytest.raises(FrozenInstanceError):
        summary.readiness_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readiness_status"):
        replace(summary, readiness_status="blocked", payload_digest="")

    with pytest.raises(TypeError):

        class ConfigSubclass(CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig):
            pass

    with pytest.raises(TypeError):

        class InputSubclass(CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput):
            pass

    with pytest.raises(TypeError):

        class ReportSubclass(CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport):
            pass


def test_module_is_pure_report_only_and_contains_no_execution_surface() -> None:
    import polymarket_alpha_lab.category_playbook_category_threshold_domain_policy_readiness as module

    assert module.__all__ == (
        "DEFAULT_CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_VERSION",
        "CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_STATUSES",
        "SUPPORTED_CATEGORY_IDS",
        "CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig",
        "CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput",
        "CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport",
        "category_playbook_category_threshold_domain_policy_readiness_config",
        "build_category_playbook_category_threshold_domain_policy_readiness_report",
        "category_playbook_category_threshold_domain_policy_readiness_payload",
    )

    source = inspect.getsource(module)
    tree = ast.parse(source)

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
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_source_terms = (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "ke" + "y",
        "si" + "gn",
        "ex" + "ec",
        "tra" + "de",
        "bu" + "y",
        "se" + "ll",
        "data" + "base",
        "per" + "sist",
        "request",
        "socket",
        "subprocess",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
