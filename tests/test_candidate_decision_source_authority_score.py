from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_source_authority_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "candidate_ref": "redacted-candidate-alpha",
        "official_source_count": d("2"),
        "primary_source_count": d("2"),
        "independent_source_count": d("3"),
        "conflicting_source_count": d("0"),
        "source_hierarchy_score": d("0.950000"),
        "recency_score": d("0.900000"),
        "reason_codes": ("local_fact_bundle_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceAuthorityScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.score_candidate_decision_source_authority(
        score_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_official_authority_passes_with_redacted_candidate_ref() -> None:
    module = api()

    row = score()

    assert row == module.CandidateDecisionSourceAuthorityScoreRow(
        candidate_ref="redacted-candidate-alpha",
        official_source_count=d("2"),
        primary_source_count=d("2"),
        independent_source_count=d("3"),
        conflicting_source_count=d("0"),
        source_hierarchy_score=d("0.950000"),
        recency_score=d("0.900000"),
        authority_score=d("0.970000"),
        authority_status="pass",
        safety_flags=module.SAFETY_FLAGS,
        reason_codes=(
            "local_fact_bundle_present",
            "candidate_decision_source_authority_score",
            "source_authority_pass",
            "official_sources_present",
            "primary_sources_present",
            "independent_sources_present",
            "no_conflicting_sources",
            "source_hierarchy_strong",
            "recency_current",
            "authority_score_meets_pass_threshold",
        ),
        derived_validation_digest=row.derived_validation_digest,
    )
    assert type(row.authority_score) is Decimal
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.safety_flags == module.SAFETY_FLAGS


def test_conflicting_sources_hard_block_even_with_high_authority() -> None:
    row = score(score_input(conflicting_source_count=d("1")))

    assert row.authority_score == d("0.970000")
    assert row.authority_status == "blocked"
    assert "source_conflict_hard_block" in row.reason_codes
    assert "conflicting_sources_present" in row.reason_codes
    assert "authority_score_blocked_by_conflict" in row.reason_codes


def test_stale_weak_authority_is_watch_not_pass() -> None:
    row = score(
        score_input(
            official_source_count=d("0"),
            primary_source_count=d("1"),
            independent_source_count=d("1"),
            source_hierarchy_score=d("0.550000"),
            recency_score=d("0.250000"),
            reason_codes=(),
        ),
    )

    assert row.authority_score == d("0.326667")
    assert row.authority_status == "watch"
    assert row.reason_codes == (
        "candidate_decision_source_authority_score",
        "source_authority_watch",
        "official_sources_absent",
        "primary_sources_present",
        "independent_sources_present",
        "no_conflicting_sources",
        "source_hierarchy_weak",
        "recency_stale",
        "authority_score_below_pass_threshold",
    )


def test_report_sorts_deterministically_and_aggregates_counts() -> None:
    module = api()
    report = module.build_candidate_decision_source_authority_score_report(
        (
            score_input(candidate_ref="redacted-candidate-z"),
            score_input(
                candidate_ref="redacted-candidate-watch",
                official_source_count=d("0"),
                primary_source_count=d("1"),
                independent_source_count=d("1"),
                source_hierarchy_score=d("0.550000"),
                recency_score=d("0.250000"),
            ),
            score_input(candidate_ref="redacted-candidate-a"),
            score_input(candidate_ref="redacted-candidate-blocked", conflicting_source_count=d("1")),
        ),
    )

    assert tuple(row.candidate_ref for row in report.rows) == (
        "redacted-candidate-blocked",
        "redacted-candidate-a",
        "redacted-candidate-z",
        "redacted-candidate-watch",
    )
    assert report.candidate_count == d("4")
    assert report.pass_count == d("2")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.max_authority_score == d("0.970000")
    assert report.min_authority_score == d("0.326667")
    assert report.average_authority_score == d("0.809167")
    assert report.report_status == "blocked"
    assert report.reason_codes[0] == "candidate_decision_source_authority_report_blocked"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_scoring_is_independent_of_ambient_decimal_context() -> None:
    module = api()
    candidates = (
        score_input(candidate_ref="redacted-candidate-alpha"),
        score_input(
            candidate_ref="redacted-candidate-watch",
            official_source_count=d("0"),
            primary_source_count=d("1"),
            independent_source_count=d("1"),
            source_hierarchy_score=d("0.550000"),
            recency_score=d("0.250000"),
        ),
    )
    expected_report = module.build_candidate_decision_source_authority_score_report(candidates)

    with localcontext() as context:
        context.prec = 2
        context.rounding = "ROUND_UP"
        actual_report = module.build_candidate_decision_source_authority_score_report(candidates)

    assert actual_report.payload == expected_report.payload


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    row = score()

    payload = row.payload

    assert payload == module.candidate_decision_source_authority_score_payload(row)
    assert payload["candidate_ref"] == "redacted-candidate-alpha"
    assert payload["authority_score"] == "0.970000"
    assert payload["official_source_count"] == "2"
    assert payload["reason_codes"] == list(row.reason_codes)
    assert payload["safety_flags"] == list(module.SAFETY_FLAGS)
    assert "market_id" not in payload
    assert "normalized_market_question" not in payload
    assert "source_refs" not in payload
    assert_no_float_values(payload)

    object.__setattr__(row, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_source_authority_score_payload(row)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.CandidateDecisionSourceAuthorityScoreConfig()
    subject = score_input()
    row = score(subject)
    report = module.build_candidate_decision_source_authority_score_report((subject,))

    assert is_dataclass(config)
    assert is_dataclass(subject)
    assert is_dataclass(row)
    assert is_dataclass(report)
    assert module.CandidateDecisionSourceAuthorityScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionSourceAuthorityScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionSourceAuthorityScoreRow.__dataclass_params__.frozen
    assert module.CandidateDecisionSourceAuthorityScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.candidate_ref = "redacted-candidate-other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.authority_status = "watch"  # type: ignore[misc]

    for instance in (config, subject, row, report):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="official_source_count must be a Decimal"):
        score_input(official_source_count=2)
    with pytest.raises(ValueError, match="official_source_count must be integral"):
        score_input(official_source_count=d("1.5"))
    with pytest.raises(ValueError, match="source_hierarchy_score must be no greater than 1"):
        score_input(source_hierarchy_score=d("1.100000"))
    with pytest.raises(ValueError, match="candidate_ref must be redacted"):
        score_input(candidate_ref="candidate-alpha")
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["local_fact_bundle_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="safety_flags must match"):
        replace(row, safety_flags=("paper_only",))
    with pytest.raises(ValueError, match="score_input"):
        score(object())
    with pytest.raises(ValueError, match="supported config version"):
        module.CandidateDecisionSourceAuthorityScoreConfig(
            config_version="candidate-decision-source-authority-score-next",
        )

    rebuilt = module.CandidateDecisionSourceAuthorityScoreRow(
        **public_field_values(row),
    )
    assert rebuilt == row


def test_public_dataclasses_reject_subclassing() -> None:
    module = api()

    for class_name in (
        "CandidateDecisionSourceAuthorityScoreConfig",
        "CandidateDecisionSourceAuthorityScoreInput",
        "CandidateDecisionSourceAuthorityScoreRow",
        "CandidateDecisionSourceAuthorityScoreReport",
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(
                f"Derived{class_name}",
                (getattr(module, class_name),),
                {},
            )


def test_rejects_unsafe_values_and_raw_reference_surfaces() -> None:
    module = api()
    unsafe_terms = (
        "recommendation",
        "recommend",
        "buy",
        "sell",
        "long_position",
        "short_position",
        "position_size",
        "position",
        "sizing",
        "stake",
        "shares",
        "contracts",
        "fill",
        "execute",
        "executed",
        "access_token",
        "api_key",
        "auth_token",
        "authorization",
        "bearer",
        "cookie",
        "csrf",
        "login",
        "signature",
        "private_key",
        "private_token",
        "token",
        "secret",
        "password",
        "credential",
        "session",
        "jwt",
        "oauth",
        "wallet",
        "account",
        "order",
        "trade",
        "trading",
        "position_sizing",
        "dsn",
        "connection_string",
        "table",
        "schema",
        "warehouse",
        "jdbc",
        "odbc",
        "postgresql",
        "mysql",
        "sqlite",
        "snowflake",
        "bigquery",
        "redshift",
        "network",
        "database",
        "persist",
        "signing",
        "exchange",
        "cancel",
        "replace",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            score_input(candidate_ref=f"redacted-candidate-{term}")
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_candidate_decision_source_authority_score_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_candidate_decision_source_authority_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )

    raw_ref_payloads = (
        {"candidate_id": "redacted-candidate-alpha"},
        {"market_id": "redacted-candidate-alpha"},
        {"market_slug": "redacted-candidate-alpha"},
        {"event_slug": "redacted-candidate-alpha"},
        {"slug": "redacted-candidate-alpha"},
        {"normalized_market_question": "redacted-candidate-alpha"},
        {"source_ref": "redacted-candidate-alpha"},
        {"source_url": "redacted-candidate-alpha"},
        {"url": "redacted-candidate-alpha"},
        {"safe_field": "https://example.test/source"},
        {"safe_field": "www.example.test/source"},
        {"safe_field": "source-id-123"},
    )
    for payload in raw_ref_payloads:
        with pytest.raises(ValueError, match="raw reference"):
            module.reject_candidate_decision_source_authority_score_unsafe_payload(
                "raw-ref-test",
                payload,
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_source_authority_score.py",
    ).read_text(encoding="utf-8")
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "subprocess",
        "getenv",
        "environ",
        "open(",
        "Path(",
        "connect(",
        "execute(",
        "commit(",
        "rollback(",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "AUTHORITY_STATUSES",
        "SAFETY_FLAGS",
        "CandidateDecisionSourceAuthorityScoreConfig",
        "CandidateDecisionSourceAuthorityScoreInput",
        "CandidateDecisionSourceAuthorityScoreRow",
        "CandidateDecisionSourceAuthorityScoreReport",
        "score_candidate_decision_source_authority",
        "build_candidate_decision_source_authority_score_report",
        "candidate_decision_source_authority_score_payload",
        "reject_candidate_decision_source_authority_score_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "candidate_decision_source_authority_score" not in getattr(
        root,
        "__all__",
        (),
    )
