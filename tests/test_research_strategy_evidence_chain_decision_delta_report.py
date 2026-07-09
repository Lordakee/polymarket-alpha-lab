from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_evidence_chain_decision_delta_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_evidence_chain_decision_delta_report.py",
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def cfg(**overrides: object) -> Any:
    values = {
        "config_version": (
            api().DEFAULT_RESEARCH_STRATEGY_EVIDENCE_CHAIN_DECISION_DELTA_REPORT_VERSION
        ),
        "pass_min_delta_score": d("0.100000"),
        "block_below_delta_score": d("-0.100000"),
        "min_pass_evidence_completeness_delta": d("0.100000"),
        "min_watch_evidence_completeness_delta": d("-0.200000"),
        "min_pass_confidence_delta": d("0.100000"),
        "min_watch_confidence_delta": d("-0.200000"),
        "max_pass_contradiction_pressure_delta": d("0.000000"),
        "max_watch_contradiction_pressure_delta": d("0.300000"),
        "max_pass_liquidity_cost_pressure": d("0.200000"),
        "max_watch_liquidity_cost_pressure": d("0.500000"),
        "max_pass_review_urgency": d("0.200000"),
        "max_watch_review_urgency": d("0.600000"),
        "evidence_completeness_delta_weight": d("0.300000"),
        "confidence_delta_weight": d("0.250000"),
        "contradiction_pressure_delta_weight": d("0.200000"),
        "liquidity_cost_pressure_weight": d("0.150000"),
        "review_urgency_weight": d("0.100000"),
    }
    values.update(overrides)
    return api().ResearchStrategyEvidenceChainDecisionDeltaConfig(**values)


def change(chain_ref: str = "chain-ref-alpha", **overrides: object) -> Any:
    values = {
        "chain_ref": chain_ref,
        "evidence_completeness_delta": d("0.300000"),
        "source_confidence_delta": d("0.200000"),
        "contradiction_pressure_delta": d("-0.200000"),
        "liquidity_cost_pressure": d("0.100000"),
        "review_urgency": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return api().ResearchStrategyEvidenceChainDecisionDeltaInput(**values)


def report(*items: Any, config: Any | None = None) -> Any:
    return api().build_research_strategy_evidence_chain_decision_delta_report(
        items,
        config=cfg() if config is None else config,
    )


def test_delta_scoring_reduces_to_pass_watch_block_analyst_rows() -> None:
    summary = report(
        change("raw-candidate-id/market-slug?token=hidden&wallet=private"),
        change(
            "watch-ref",
            evidence_completeness_delta=d("0.150000"),
            source_confidence_delta=d("0.100000"),
            contradiction_pressure_delta=d("0.050000"),
            liquidity_cost_pressure=d("0.250000"),
            review_urgency=d("0.300000"),
        ),
        change(
            "block-ref",
            evidence_completeness_delta=d("-0.300000"),
            source_confidence_delta=d("-0.250000"),
            contradiction_pressure_delta=d("0.500000"),
            liquidity_cost_pressure=d("0.700000"),
            review_urgency=d("0.800000"),
        ),
    )

    assert is_dataclass(summary)
    assert type(summary) is api().ResearchStrategyEvidenceChainDecisionDeltaReport
    assert summary.config_version == (
        api().DEFAULT_RESEARCH_STRATEGY_EVIDENCE_CHAIN_DECISION_DELTA_REPORT_VERSION
    )
    assert summary.status == "block"
    assert summary.row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_delta_score == d("-0.096667")
    assert summary.min_delta_score == d("-0.437500")
    assert summary.max_delta_score == d("0.155000")
    assert summary.max_liquidity_cost_pressure == d("0.700000")
    assert summary.max_review_urgency == d("0.800000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert blocked.delta_score == d("-0.437500")
    assert blocked.reason_codes == (
        "evidence_completeness_deteriorated_block",
        "confidence_deteriorated_block",
        "contradiction_pressure_increased_block",
        "liquidity_cost_pressure_block",
        "review_urgency_block",
        "decision_delta_score_block",
    )

    watched = summary.rows[1]
    assert watched.delta_score == d("-0.007500")
    assert watched.reason_codes == (
        "contradiction_pressure_increased_watch",
        "liquidity_cost_pressure_watch",
        "review_urgency_watch",
        "decision_delta_score_watch",
    )

    passed = summary.rows[2]
    assert passed.delta_score == d("0.155000")
    assert passed.reason_codes == ("decision_readiness_delta_pass",)
    assert tuple(count.reason_code for count in summary.reason_code_counts[:3]) == (
        "confidence_deteriorated_block",
        "contradiction_pressure_increased_block",
        "contradiction_pressure_increased_watch",
    )


def test_status_boundaries_treat_exact_pass_as_pass_and_exact_block_as_watch() -> None:
    boundary_cfg = cfg(
        min_pass_evidence_completeness_delta=d("-1.000000"),
        min_watch_evidence_completeness_delta=d("-1.000000"),
        min_pass_confidence_delta=d("-1.000000"),
        min_watch_confidence_delta=d("-1.000000"),
        max_pass_contradiction_pressure_delta=d("1.000000"),
        max_watch_contradiction_pressure_delta=d("1.000000"),
        max_pass_liquidity_cost_pressure=d("1.000000"),
        max_watch_liquidity_cost_pressure=d("1.000000"),
        max_pass_review_urgency=d("1.000000"),
        max_watch_review_urgency=d("1.000000"),
        evidence_completeness_delta_weight=d("1.000000"),
        confidence_delta_weight=d("0.000000"),
        contradiction_pressure_delta_weight=d("0.000000"),
        liquidity_cost_pressure_weight=d("0.000000"),
        review_urgency_weight=d("0.000000"),
    )

    pass_boundary = report(
        change("pass-boundary", evidence_completeness_delta=d("0.100000")),
        config=boundary_cfg,
    )
    watch_boundary = report(
        change("watch-boundary", evidence_completeness_delta=d("-0.100000")),
        config=boundary_cfg,
    )

    assert pass_boundary.rows[0].delta_score == d("0.100000")
    assert pass_boundary.rows[0].status == "pass"
    assert watch_boundary.rows[0].delta_score == d("-0.100000")
    assert watch_boundary.rows[0].status == "watch"


def test_builder_rejects_falsy_non_config_values() -> None:
    with pytest.raises(ValueError, match="config"):
        api().build_research_strategy_evidence_chain_decision_delta_report(
            (),
            config=False,  # type: ignore[arg-type]
        )


def test_public_payload_is_deterministic_digest_validated_and_json_safe() -> None:
    items = (
        change("chain-ref-c", contradiction_pressure_delta=d("0.500000")),
        change("chain-ref-a"),
        change("chain-ref-b", evidence_completeness_delta=d("0.150000")),
    )
    summary_a = report(*items)
    summary_b = report(*reversed(items))
    payload_a = api().research_strategy_evidence_chain_decision_delta_public_payload(
        summary_a,
    )
    payload_b = api().research_strategy_evidence_chain_decision_delta_public_payload(
        summary_b,
    )

    assert payload_a == payload_b
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert api().research_strategy_evidence_chain_decision_delta_digest(summary_a) == (
        payload_a["derived_validation_digest"]
    )
    assert payload_a["row_count"] == "3.000000"
    assert payload_a["rows"][0]["status"] == "block"
    assert _float_paths(payload_a) == ()
    json.dumps(payload_a, sort_keys=True)

    tampered = dict(payload_a)
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(tampered)


def test_signed_zero_is_canonicalized_before_public_digest() -> None:
    positive = report(
        change(
            "same-chain",
            evidence_completeness_delta=d("0"),
            source_confidence_delta=d("0"),
            contradiction_pressure_delta=d("0"),
            liquidity_cost_pressure=d("0"),
            review_urgency=d("0"),
        ),
    )
    negative = report(
        change(
            "same-chain",
            evidence_completeness_delta=d("-0"),
            source_confidence_delta=d("-0"),
            contradiction_pressure_delta=d("-0"),
            liquidity_cost_pressure=d("-0"),
            review_urgency=d("-0"),
        ),
    )

    positive_payload = positive.public_payload
    negative_payload = negative.public_payload

    assert negative_payload == positive_payload
    assert negative.derived_validation_digest == positive.derived_validation_digest
    assert "-0.000000" not in json.dumps(negative_payload, sort_keys=True)


def test_payload_prevents_raw_identifier_and_unsafe_surface_leaks() -> None:
    private_input = change(
        "raw-candidate-id/market-slug?token=hidden&wallet=private",
    )
    summary = report(private_input)
    payload = api().research_strategy_evidence_chain_decision_delta_public_payload(
        summary,
    )
    rendered = repr(payload).casefold()
    raw_rendered = repr(summary).casefold()
    input_rendered = repr(private_input).casefold()

    for leaked in (
        "raw-candidate-id",
        "market-slug",
        "token=hidden",
        "wallet=private",
        "source_url",
        "source_text",
        "https://",
        "postgres://",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "buy",
        "sell",
    ):
        assert leaked not in rendered
        if leaked in {"raw-candidate-id", "market-slug", "token=hidden", "wallet=private"}:
            assert leaked not in raw_rendered
            assert leaked not in input_rendered

    for unsafe_key, unsafe_value in (
        ("candidate_id", "opaque"),
        ("market_slug", "will-fed-cut-rates"),
        ("market_question", "Will this happen?"),
        ("source_url", "https://example.test/evidence"),
        ("sourceURL", "redacted"),
        ("source_text", "raw copied source text"),
        ("sourceText", "redacted"),
        ("dsn", "postgres://example"),
        ("wallet", "0xabc"),
        ("order_ticket", "abc"),
        ("execute_surface", "paper"),
        ("execution_surface", "paper"),
        ("liveSurface", "disabled"),
        ("live_trading", "disabled"),
        ("liveTrading", "disabled"),
        ("trading_surface", "paper"),
        ("api_key", "opaque"),
        ("private_key", "opaque"),
        ("secret", "opaque"),
        ("db_uri", "redacted"),
        ("network_surface", "disabled"),
        ("sizing", "100"),
        ("recommendation", "buy"),
        ("public_note", "live execution disabled"),
        ("public_note", "live trading disabled"),
        ("public_note", "postgresql read model"),
    ):
        leaked = dict(payload)
        leaked[unsafe_key] = unsafe_value
        leaked["derived_validation_digest"] = canonical_digest(leaked)
        with pytest.raises(ValueError, match="unsafe public"):
            api().research_strategy_evidence_chain_decision_delta_public_payload(leaked)

    numeric = dict(payload)
    numeric["row_count"] = 3
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="numeric"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    downgraded["derived_validation_digest"] = canonical_digest(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(downgraded)

    bad_status = dict(payload)
    bad_status["status"] = ["pass"]
    bad_status["derived_validation_digest"] = canonical_digest(bad_status)
    with pytest.raises(ValueError, match="status"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(bad_status)


def test_public_payload_requires_exact_nested_schema_and_consistent_values() -> None:
    payload = api().research_strategy_evidence_chain_decision_delta_public_payload(
        report(change()),
    )

    extra_report_field = dict(payload)
    extra_report_field["analyst_note"] = "redacted"
    extra_report_field["derived_validation_digest"] = canonical_digest(
        extra_report_field,
    )
    with pytest.raises(ValueError, match="unexpected public payload field"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(
            extra_report_field,
        )

    missing_report_field = dict(payload)
    missing_report_field.pop("max_review_urgency")
    missing_report_field["derived_validation_digest"] = canonical_digest(
        missing_report_field,
    )
    with pytest.raises(ValueError, match="missing public payload field"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(
            missing_report_field,
        )

    inconsistent_count = dict(payload)
    inconsistent_count["row_count"] = "2.000000"
    inconsistent_count["derived_validation_digest"] = canonical_digest(
        inconsistent_count,
    )
    with pytest.raises(ValueError, match="row_count"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(
            inconsistent_count,
        )

    malformed_decimal = dict(payload)
    malformed_decimal["average_delta_score"] = "not-a-decimal"
    malformed_decimal["derived_validation_digest"] = canonical_digest(
        malformed_decimal,
    )
    with pytest.raises(ValueError, match="average_delta_score"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(
            malformed_decimal,
        )

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["analyst_note"] = "redacted"
    extra_row_field["derived_validation_digest"] = canonical_digest(extra_row_field)
    with pytest.raises(ValueError, match="unexpected public payload field"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(
            extra_row_field,
        )

    missing_reason_count_field = json.loads(json.dumps(payload))
    missing_reason_count_field["reason_code_counts"][0].pop("row_ratio")
    missing_reason_count_field["derived_validation_digest"] = canonical_digest(
        missing_reason_count_field,
    )
    with pytest.raises(ValueError, match="missing public payload field"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(
            missing_reason_count_field,
        )

    unsupported_reason_code = json.loads(json.dumps(payload))
    unsupported_reason_code["rows"][0]["reason_codes"] = ["unrecognized_safe_code"]
    unsupported_reason_code["derived_validation_digest"] = canonical_digest(
        unsupported_reason_code,
    )
    with pytest.raises(ValueError, match="reason_codes"):
        api().research_strategy_evidence_chain_decision_delta_public_payload(
            unsupported_reason_code,
        )


def test_custom_config_validation_decimal_strictness_and_frozen_flags() -> None:
    module = api()
    custom = cfg(
        pass_min_delta_score=d("0.050000"),
        block_below_delta_score=d("-0.050000"),
        min_pass_evidence_completeness_delta=d("0.050000"),
        min_pass_confidence_delta=d("0.050000"),
        max_pass_liquidity_cost_pressure=d("0.500000"),
        max_watch_liquidity_cost_pressure=d("0.800000"),
        max_pass_review_urgency=d("0.500000"),
        max_watch_review_urgency=d("0.800000"),
        evidence_completeness_delta_weight=d("0.500000"),
        confidence_delta_weight=d("0.500000"),
        contradiction_pressure_delta_weight=d("0.000000"),
        liquidity_cost_pressure_weight=d("0.000000"),
        review_urgency_weight=d("0.000000"),
    )
    summary = report(
        change(
            "custom-pass",
            evidence_completeness_delta=d("0.050000"),
            source_confidence_delta=d("0.050000"),
            liquidity_cost_pressure=d("0.400000"),
            review_urgency=d("0.400000"),
        ),
        config=custom,
    )

    assert summary.rows[0].delta_score == d("0.050000")
    assert summary.rows[0].status == "pass"

    for value in (custom, change(), summary, *summary.rows, *summary.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(
                ("_count", "_score", "_delta", "_pressure", "_urgency", "_weight"),
            ):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        summary.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].delta_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        cfg(config_version=_StringSubclass(module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_CHAIN_DECISION_DELTA_REPORT_VERSION))
    with pytest.raises(ValueError, match="pass_min_delta_score"):
        cfg(pass_min_delta_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_confidence_delta"):
        change(source_confidence_delta=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="weights"):
        cfg(evidence_completeness_delta_weight=d("0.400000"))
    with pytest.raises(ValueError, match="pass_min_delta_score"):
        cfg(pass_min_delta_score=d("-0.200000"))
    with pytest.raises(ValueError, match="max_pass_liquidity_cost_pressure"):
        cfg(max_pass_liquidity_cost_pressure=d("0.700000"))
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        change(readonly=False)
    with pytest.raises(ValueError, match="chain_ref"):
        change(_StringSubclass("chain-ref-alpha"))
    with pytest.raises(ValueError, match="chain_ref"):
        change("")
    with pytest.raises(ValueError, match="inputs"):
        module.build_research_strategy_evidence_chain_decision_delta_report(
            (object(),),
            config=cfg(),
        )
    with pytest.raises(ValueError, match="pass_count"):
        replace(summary, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)


def test_public_api_is_report_only_and_has_no_external_execution_surfaces() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_CHAIN_DECISION_DELTA_REPORT_VERSION",
        "ResearchStrategyEvidenceChainDecisionDeltaConfig",
        "ResearchStrategyEvidenceChainDecisionDeltaInput",
        "ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount",
        "ResearchStrategyEvidenceChainDecisionDeltaReport",
        "ResearchStrategyEvidenceChainDecisionDeltaRow",
        "build_research_strategy_evidence_chain_decision_delta_report",
        "research_strategy_evidence_chain_decision_delta_digest",
        "research_strategy_evidence_chain_decision_delta_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "http",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
        "write_bytes",
        "write_text",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    if isinstance(value, float):
        return (path,)
    return ()
