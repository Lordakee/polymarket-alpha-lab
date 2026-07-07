from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_evidence_staleness_score"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_EVIDENCE_STALENESS_SCORE_CONFIG_VERSION
        ),
        "max_pass_evidence_staleness_score": d("0.250000"),
        "max_watch_evidence_staleness_score": d("0.500000"),
        "max_pass_newest_evidence_age_hours": d("24.000000"),
        "max_watch_newest_evidence_age_hours": d("72.000000"),
        "max_pass_average_evidence_age_hours": d("48.000000"),
        "max_watch_average_evidence_age_hours": d("168.000000"),
        "max_pass_prior_research_age_hours": d("24.000000"),
        "max_watch_prior_research_age_hours": d("72.000000"),
        "max_pass_stale_source_ratio": d("0.250000"),
        "max_watch_stale_source_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.CandidateDecisionEvidenceStalenessScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "source_count": d("4"),
        "stale_source_count": d("0"),
        "newest_evidence_age_hours": d("4.000000"),
        "average_evidence_age_hours": d("12.000000"),
        "oldest_evidence_age_hours": d("36.000000"),
        "prior_research_age_hours": d("6.000000"),
        "reason_codes": ("local_evidence_age_metrics_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionEvidenceStalenessScoreInput(**values)


def report(subject: object | None = None, cfg: object | None = None):
    module = api()
    return module.build_candidate_decision_evidence_staleness_score_report(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_public_numbers(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected Decimal value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_current_evidence_staleness_passes_without_refresh_pressure() -> None:
    module = api()

    staleness_report = report()

    assert type(staleness_report) is module.CandidateDecisionEvidenceStalenessScoreReport
    assert staleness_report.source_count == d("4")
    assert staleness_report.stale_source_count == d("0")
    assert staleness_report.stale_source_ratio == d("0.000000")
    assert staleness_report.newest_evidence_staleness_component == d("0.000000")
    assert staleness_report.average_evidence_staleness_component == d("0.000000")
    assert staleness_report.prior_research_staleness_component == d("0.000000")
    assert staleness_report.stale_source_ratio_component == d("0.000000")
    assert staleness_report.evidence_staleness_score == d("0.000000")
    assert staleness_report.staleness_status == "pass"
    assert staleness_report.hard_blocker_codes == ()
    assert staleness_report.reason_codes == (
        "local_evidence_age_metrics_present",
        "candidate_decision_evidence_staleness_score",
        "staleness_pass",
        "newest_evidence_age_pass",
        "average_evidence_age_pass",
        "prior_research_age_pass",
        "stale_source_ratio_pass",
        "research_refresh_not_required",
    )
    assert staleness_report.paper_only is True
    assert staleness_report.report_only is True
    assert staleness_report.readonly is True
    assert_sha256(staleness_report.derived_validation_digest)


def test_aging_evidence_watches_for_research_refresh() -> None:
    staleness_report = report(
        score_input(
            stale_source_count=d("1"),
            newest_evidence_age_hours=d("48.000000"),
            average_evidence_age_hours=d("96.000000"),
            oldest_evidence_age_hours=d("120.000000"),
            prior_research_age_hours=d("48.000000"),
            reason_codes=(),
        ),
    )

    assert staleness_report.stale_source_ratio == d("0.250000")
    assert staleness_report.newest_evidence_staleness_component == d("0.500000")
    assert staleness_report.average_evidence_staleness_component == d("0.400000")
    assert staleness_report.prior_research_staleness_component == d("0.500000")
    assert staleness_report.stale_source_ratio_component == d("0.000000")
    assert staleness_report.evidence_staleness_score == d("0.350000")
    assert staleness_report.staleness_status == "watch"
    assert staleness_report.hard_blocker_codes == ()
    assert staleness_report.reason_codes == (
        "candidate_decision_evidence_staleness_score",
        "staleness_watch",
        "newest_evidence_age_watch",
        "average_evidence_age_watch",
        "prior_research_age_watch",
        "stale_source_ratio_pass",
        "research_refresh_watch",
    )


def test_stale_evidence_blocks_until_research_refresh() -> None:
    staleness_report = report(
        score_input(
            stale_source_count=d("3"),
            newest_evidence_age_hours=d("80.000000"),
            average_evidence_age_hours=d("200.000000"),
            oldest_evidence_age_hours=d("240.000000"),
            prior_research_age_hours=d("90.000000"),
            reason_codes=(),
        ),
    )

    assert staleness_report.stale_source_ratio == d("0.750000")
    assert staleness_report.evidence_staleness_score == d("1.000000")
    assert staleness_report.staleness_status == "block"
    assert staleness_report.hard_blocker_codes == (
        "newest_evidence_age_block",
        "average_evidence_age_block",
        "prior_research_age_block",
        "stale_source_ratio_block",
        "evidence_staleness_score_block",
    )
    assert staleness_report.reason_codes == (
        "candidate_decision_evidence_staleness_score",
        "staleness_block",
        "newest_evidence_age_block",
        "average_evidence_age_block",
        "prior_research_age_block",
        "stale_source_ratio_block",
        "research_refresh_required",
        "evidence_staleness_score_block",
    )


def test_dataclasses_are_frozen_decimal_exact_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    staleness_report = report(subject, cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(staleness_report)
    assert module.CandidateDecisionEvidenceStalenessScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionEvidenceStalenessScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionEvidenceStalenessScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.source_count = d("9")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        staleness_report.staleness_status = "watch"  # type: ignore[misc]

    for instance in (cfg, subject, staleness_report):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        score_input(source_count=4)
    with pytest.raises(ValueError, match="newest_evidence_age_hours must be a Decimal"):
        score_input(newest_evidence_age_hours=4.0)
    with pytest.raises(ValueError, match="newest_evidence_age_hours must be an exact Decimal"):
        score_input(newest_evidence_age_hours=DecimalSubclass("4.000000"))
    with pytest.raises(ValueError, match="stale_source_count must not exceed source_count"):
        score_input(stale_source_count=d("5"))
    with pytest.raises(ValueError, match="oldest_evidence_age_hours must not be less"):
        score_input(oldest_evidence_age_hours=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["local_evidence_age_metrics_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(staleness_report, readonly=False)
    with pytest.raises(ValueError, match="Input"):
        report(object())
    with pytest.raises(ValueError, match="Config"):
        report(score_input(), object())

    rebuilt_input = module.CandidateDecisionEvidenceStalenessScoreInput(
        **public_field_values(subject),
    )
    rebuilt_report = module.CandidateDecisionEvidenceStalenessScoreReport(
        **public_field_values(staleness_report),
    )
    assert rebuilt_input == subject
    assert rebuilt_report == staleness_report


def test_payload_is_deterministic_json_ready_and_redacted() -> None:
    module = api()
    first = report()
    second = report(score_input())

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest

    payload = module.candidate_decision_evidence_staleness_score_payload(first)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload == first.payload
    assert payload["source_count"] == "4"
    assert payload["stale_source_ratio"] == "0.000000"
    assert payload["evidence_staleness_score"] == "0.000000"
    assert payload["staleness_status"] == "pass"
    assert payload["reason_codes"] == list(first.reason_codes)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numbers(payload)

    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "raw_text",
        "http",
        "www.",
        "dsn",
        "table_name",
        "auth_token",
        "token",
        "wallet",
        "order",
        "trade",
        "position_size",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in rendered


def test_public_payload_validator_rejects_leaks_and_status_aliases() -> None:
    module = api()

    unsafe_payloads = (
        ({"candidate_id": "raw-candidate-alpha"}, "raw candidate"),
        ({"market_id": "market-alpha"}, "raw market"),
        ({"market_slug": "market-alpha"}, "raw market"),
        ({"question": "will this event happen"}, "raw market"),
        ({"source_ref": "source-ref:abc123"}, "source refs"),
        ({"source_url": "https://example.test/source"}, "source refs"),
        ({"source_text": "raw source text"}, "source refs"),
        ({"safe_key": "https://example.test/source"}, "source refs"),
        ({"safe_key": "orders_table"}, "unsafe live surface"),
        ({"safe_key": "api-token"}, "unsafe live surface"),
        ({"safe_key": "wallet auth order trade"}, "unsafe live surface"),
        ({"safe_key": "position_size"}, "unsafe live surface"),
        ({"safe_key": "buy sell recommendation"}, "unsafe live surface"),
        ({"safe_key": "仓位"}, "unsafe live surface"),
        ({"staleness_status": "blocked"}, "public status"),
        ({"staleness_status": "ready"}, "public status"),
        ({"safe_key": "matched"}, "public status"),
        ({"source_count": 1}, "decimal strings"),
        ({"source_count": 1.0}, "decimal strings"),
        (["not", "object"], "public payload must be a JSON object"),
    )

    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_evidence_staleness_score_public_payload(
                payload,
            )

    for unsafe_reason_code in (
        "candidate_id_raw",
        "market_slug_raw",
        "source_url_raw",
        "orders_table",
        "wallet_auth_order_trade",
        "buy_sell_recommendation",
        "position_size_raw",
    ):
        with pytest.raises(ValueError, match="unsafe|raw|source refs"):
            score_input(reason_codes=(unsafe_reason_code,))


def test_report_digest_consistency_rejects_mutations() -> None:
    module = api()
    staleness_report = report()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionEvidenceStalenessScoreReport(
            **{
                **public_field_values(staleness_report),
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="evidence_staleness_score"):
        replace(
            staleness_report,
            evidence_staleness_score=d("0.500000"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="staleness_status"):
        replace(
            staleness_report,
            staleness_status="blocked",
            derived_validation_digest="",
        )

    object.__setattr__(staleness_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_evidence_staleness_score_payload(staleness_report)

    assert module.STALENESS_STATUSES == ("pass", "watch", "block")
    assert set(module.STALENESS_STATUSES) == {"pass", "watch", "block"}


def test_module_has_no_io_network_persistence_or_live_trading_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_EVIDENCE_STALENESS_SCORE_CONFIG_VERSION",
        "STALENESS_STATUSES",
        "CandidateDecisionEvidenceStalenessScoreConfig",
        "CandidateDecisionEvidenceStalenessScoreInput",
        "CandidateDecisionEvidenceStalenessScoreReport",
        "build_candidate_decision_evidence_staleness_score_report",
        "candidate_decision_evidence_staleness_score_payload",
        "validate_candidate_decision_evidence_staleness_score_public_payload",
        "reject_candidate_decision_evidence_staleness_score_unsafe_payload",
    )

    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "ccxt",
        "os",
        "pathlib",
        "subprocess",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "submit",
        "execute",
        "commit",
        "rollback",
        "getenv",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_call_names
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_call_names
