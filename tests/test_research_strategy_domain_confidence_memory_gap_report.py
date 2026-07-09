from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_domain_confidence_memory_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_domain_confidence_memory_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-strategy-domain-confidence-memory-gap-report-test",
        "calibration_freshness_pass_ceiling_seconds": d("2592000.000000"),
        "calibration_freshness_watch_ceiling_seconds": d("7776000.000000"),
        "historical_forecast_error_pass_ceiling": d("0.100000"),
        "historical_forecast_error_watch_ceiling": d("0.250000"),
        "evidence_confidence_pass_floor": d("0.800000"),
        "evidence_confidence_watch_floor": d("0.550000"),
        "source_disagreement_pass_ceiling": d("0.100000"),
        "source_disagreement_watch_ceiling": d("0.300000"),
        "liquidity_cost_pressure_pass_ceiling": d("0.020000"),
        "liquidity_cost_pressure_watch_ceiling": d("0.060000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainConfidenceMemoryGapConfig(**values)


def memory_input(**overrides: object):
    module = api()
    values = {
        "domain_key": "policy-events",
        "analyst_group": "policy-analysts",
        "private_candidate_reference": "candidate_alpha_raw_id",
        "private_market_reference": "market_alpha_raw_id",
        "private_market_slug_text": "market-alpha-slug",
        "private_question_text": "Will alpha resolve yes?",
        "private_evidence_locator": "https://example.invalid/private-alpha?dsn=hidden",
        "private_evidence_excerpt": (
            "Private alpha source text with access_token, wallet, order, trade, "
            "recommendation, and sizing terms."
        ),
        "calibration_updated_at": GENERATED_AT - timedelta(days=10),
        "historical_forecast_error": d("0.060000"),
        "evidence_confidence_score": d("0.900000"),
        "source_disagreement_score": d("0.040000"),
        "liquidity_cost_pressure_score": d("0.010000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainConfidenceMemoryGapInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_domain_confidence_memory_gap_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk(nested))
    return (value,)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_gap_scoring_uses_freshness_error_evidence_disagreement_and_cost() -> None:
    summary = build_report(
        memory_input(domain_key="policy-events", analyst_group="policy-pass"),
        memory_input(
            domain_key="rates-events",
            analyst_group="macro-watch",
            private_candidate_reference="candidate_beta_raw_id",
            private_market_reference="market_beta_raw_id",
            calibration_updated_at=GENERATED_AT - timedelta(days=60),
            historical_forecast_error=d("0.180000"),
            evidence_confidence_score=d("0.700000"),
            source_disagreement_score=d("0.180000"),
            liquidity_cost_pressure_score=d("0.040000"),
        ),
        memory_input(
            domain_key="crypto-events",
            analyst_group="crypto-block",
            private_candidate_reference="candidate_gamma_raw_id",
            private_market_reference="market_gamma_raw_id",
            calibration_updated_at=GENERATED_AT - timedelta(days=120),
            historical_forecast_error=d("0.320000"),
            evidence_confidence_score=d("0.400000"),
            source_disagreement_score=d("0.450000"),
            liquidity_cost_pressure_score=d("0.080000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_domain_confidence_memory_score == d("0.511111")
    assert summary.mean_memory_gap_score == d("0.488889")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "domain_confidence_memory_gap_report_block",
        "calibration_refresh_review",
        "forecast_error_review",
        "evidence_confidence_review",
        "source_disagreement_review",
        "liquidity_cost_pressure_review",
    )
    assert tuple(row.domain_key for row in summary.rows) == (
        "crypto-events",
        "rates-events",
        "policy-events",
    )

    blocked, watched, passed = summary.rows
    assert blocked.row_number == d("1.000000")
    assert blocked.status == "block"
    assert blocked.calibration_age_seconds == d("10368000.000000")
    assert blocked.calibration_freshness_score == d("0.000000")
    assert blocked.forecast_error_safety_score == d("0.000000")
    assert blocked.evidence_confidence_quality_score == d("0.000000")
    assert blocked.source_agreement_score == d("0.000000")
    assert blocked.liquidity_cost_safety_score == d("0.000000")
    assert blocked.domain_confidence_memory_score == d("0.000000")
    assert blocked.memory_gap_score == d("1.000000")
    assert blocked.reason_codes == (
        "domain_confidence_memory_gap_block",
        "calibration_freshness_block",
        "historical_forecast_error_block",
        "evidence_confidence_block",
        "source_disagreement_block",
        "liquidity_cost_pressure_block",
    )

    assert watched.status == "watch"
    assert watched.calibration_freshness_score == d("0.500000")
    assert watched.forecast_error_safety_score == d("0.466667")
    assert watched.evidence_confidence_quality_score == d("0.600000")
    assert watched.source_agreement_score == d("0.600000")
    assert watched.liquidity_cost_safety_score == d("0.500000")
    assert watched.domain_confidence_memory_score == d("0.533333")
    assert watched.memory_gap_score == d("0.466667")

    assert passed.status == "pass"
    assert passed.domain_confidence_memory_score == d("1.000000")
    assert passed.memory_gap_score == d("0.000000")
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True


def test_memory_threshold_boundaries_are_inclusive_for_pass_and_watch() -> None:
    summary = build_report(
        memory_input(
            domain_key="pass-boundary",
            calibration_updated_at=GENERATED_AT - timedelta(days=30),
            historical_forecast_error=d("0.100000"),
            evidence_confidence_score=d("0.800000"),
            source_disagreement_score=d("0.100000"),
            liquidity_cost_pressure_score=d("0.020000"),
        ),
        memory_input(
            domain_key="watch-boundary",
            private_candidate_reference="candidate_watch_boundary",
            calibration_updated_at=GENERATED_AT - timedelta(days=90),
            historical_forecast_error=d("0.250000"),
            evidence_confidence_score=d("0.550000"),
            source_disagreement_score=d("0.300000"),
            liquidity_cost_pressure_score=d("0.060000"),
        ),
        memory_input(
            domain_key="block-boundary",
            private_candidate_reference="candidate_block_boundary",
            calibration_updated_at=GENERATED_AT - timedelta(days=90, seconds=1),
            historical_forecast_error=d("0.250000"),
            evidence_confidence_score=d("0.550000"),
            source_disagreement_score=d("0.300000"),
            liquidity_cost_pressure_score=d("0.060000"),
        ),
    )

    rows = {row.domain_key: row for row in summary.rows}
    assert rows["pass-boundary"].status == "pass"
    assert rows["pass-boundary"].memory_gap_score == d("0.000000")
    assert rows["watch-boundary"].status == "watch"
    assert rows["watch-boundary"].memory_gap_score == d("1.000000")
    assert rows["block-boundary"].status == "block"
    assert "calibration_freshness_block" in rows["block-boundary"].reason_codes


def test_public_payload_is_deterministic_digest_guarded_and_leak_free() -> None:
    module = api()
    generated_at = datetime(2026, 7, 9, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = module.research_strategy_domain_confidence_memory_gap_report_payload(
        build_report(memory_input(), generated_at=generated_at),
    )
    second_payload = module.research_strategy_domain_confidence_memory_gap_report_payload(
        build_report(memory_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["domain_confidence_memory_score"] == "1.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert len(first_payload["rows"][0]["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal) for value in walk(first_payload)
    )

    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "candidate_alpha_raw_id",
        "market_alpha_raw_id",
        "market-alpha-slug",
        "will alpha resolve yes",
        "https://example.invalid/private-alpha",
        "private alpha source text",
        "dsn=",
        "access_token",
        "wallet",
        "order",
        "trade",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in payload_text

    tampered = json.loads(json.dumps(first_payload))
    tampered["rows"][0]["memory_gap_score"] = "0.123456"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_domain_confidence_memory_gap_report_payload(tampered)

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_domain_confidence_memory_gap_report_payload(
            {
                "access_" + "token": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_custom_config_validation_and_empty_report() -> None:
    module = api()
    custom = config(
        evidence_confidence_pass_floor=d("0.950000"),
        evidence_confidence_watch_floor=d("0.700000"),
        liquidity_cost_pressure_pass_ceiling=d("0.010000"),
        liquidity_cost_pressure_watch_ceiling=d("0.050000"),
    )
    summary = build_report(memory_input(), cfg=custom)
    empty = build_report(cfg=custom)

    assert summary.status == "watch"
    assert summary.rows[0].status == "watch"
    assert "evidence_confidence_watch" in summary.rows[0].reason_codes
    assert empty.input_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.block_count == d("0.000000")
    assert empty.mean_memory_gap_score == d("0.000000")
    assert empty.status == "block"
    assert empty.reason_codes == ("domain_confidence_memory_gap_report_empty",)
    assert empty.reason_code_counts == (
        module.ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount(
            reason_code="domain_confidence_memory_gap_report_empty",
            count=d("1.000000"),
            input_ratio=d("1.000000"),
        ),
    )

    with pytest.raises(ValueError, match="calibration_freshness_pass_ceiling_seconds"):
        config(
            calibration_freshness_pass_ceiling_seconds=d("7776001.000000"),
            calibration_freshness_watch_ceiling_seconds=d("7776000.000000"),
        )
    with pytest.raises(ValueError, match="evidence_confidence_watch_floor"):
        config(
            evidence_confidence_pass_floor=d("0.700000"),
            evidence_confidence_watch_floor=d("0.800000"),
        )
    with pytest.raises(ValueError, match="historical_forecast_error"):
        config(historical_forecast_error_pass_ceiling=0.1)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_validate_integrity() -> None:
    module = api()
    summary = build_report(memory_input())
    row = summary.rows[0]

    assert module.RESEARCH_STRATEGY_DOMAIN_CONFIDENCE_MEMORY_GAP_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    for value in (
        config(),
        memory_input(),
        row,
        summary,
        *summary.reason_code_counts,
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            memory_gap_score=d("0.250000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="source_disagreement_score"):
        memory_input(source_disagreement_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            memory_input(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_report(
            memory_input(domain_key="same-domain", analyst_group="same-analyst"),
            memory_input(
                domain_key="same-domain",
                analyst_group="same-analyst",
                private_candidate_reference="candidate_other_raw_id",
            ),
        )


def test_module_scope_has_no_external_or_actionable_surfaces() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_CONFIDENCE_MEMORY_GAP_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_DOMAIN_CONFIDENCE_MEMORY_GAP_REPORT_STATUSES",
        "ResearchStrategyDomainConfidenceMemoryGapConfig",
        "ResearchStrategyDomainConfidenceMemoryGapInput",
        "ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount",
        "ResearchStrategyDomainConfidenceMemoryGapRow",
        "ResearchStrategyDomainConfidenceMemoryGapReport",
        "build_research_strategy_domain_confidence_memory_gap_report",
        "research_strategy_domain_confidence_memory_gap_report_digest",
        "research_strategy_domain_confidence_memory_gap_report_payload",
    )

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
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
    assert not (call_names & forbidden_call_names)

    module_source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_source_terms = (
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "open(",
        "create_" + "order",
        "cancel_" + "order",
        "post(",
        "wal" + "let",
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "trad" + "e",
    )
    assert all(term not in module_source for term in forbidden_source_terms)
