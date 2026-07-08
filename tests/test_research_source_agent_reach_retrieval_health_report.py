from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_agent_reach_retrieval_health_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.research_source_agent_reach_retrieval_health_report",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"expected report module to exist: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_freshness_age_seconds": d("86400.000000"),
        "block_freshness_age_seconds": d("259200.000000"),
        "min_evidence_diversity_watch_ratio": d("0.750000"),
        "min_evidence_diversity_block_ratio": d("0.500000"),
        "min_source_quorum_watch_ratio": d("0.750000"),
        "min_source_quorum_block_ratio": d("0.500000"),
        "max_failed_retrieval_watch_ratio": d("0.250000"),
        "max_failed_retrieval_block_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourceAgentReachRetrievalHealthConfig(**values)


def input_row(
    retrieval_batch_ref: str,
    *,
    freshness_age_seconds: Decimal = d("900.000000"),
    evidence_family_count: Decimal = d("4.000000"),
    required_evidence_family_count: Decimal = d("4.000000"),
    source_quorum_count: Decimal = d("3.000000"),
    required_source_quorum_count: Decimal = d("3.000000"),
    retrieval_attempt_count: Decimal = d("4.000000"),
    failed_retrieval_count: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAgentReachRetrievalHealthInput(
        retrieval_batch_ref=retrieval_batch_ref,
        freshness_age_seconds=freshness_age_seconds,
        evidence_family_count=evidence_family_count,
        required_evidence_family_count=required_evidence_family_count,
        source_quorum_count=source_quorum_count,
        required_source_quorum_count=required_source_quorum_count,
        retrieval_attempt_count=retrieval_attempt_count,
        failed_retrieval_count=failed_retrieval_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_agent_reach_retrieval_health_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def _walk_payload_values(value: object) -> list[object]:
    values: list[object] = [value]
    if type(value) is dict:
        for key, item in value.items():
            values.extend(_walk_payload_values(key))
            values.extend(_walk_payload_values(item))
    elif type(value) is list:
        for item in value:
            values.extend(_walk_payload_values(item))
    return values


def _assert_payload_has_no_raw_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        pytest.fail(f"public payload leaked raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            _assert_payload_has_no_raw_numbers(item)
    elif type(value) is list:
        for item in value:
            _assert_payload_has_no_raw_numbers(item)


def _assert_payload_has_no_forbidden_text(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).casefold()
    for forbidden in (
        "safe-pass",
        "safe-watch",
        "safe-block",
        "raw candidate",
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in rendered


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_agent_reach_retrieval_health_blocks_report_only_public_payload() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceAgentReachRetrievalHealthReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.attention_count == d("0.000000")
    assert report.failed_retrieval_pressure_ratio == d("0.000000")
    assert report.avg_evidence_diversity_ratio == d("0.000000")
    assert report.avg_source_quorum_ratio == d("0.000000")
    assert report.min_retrieval_health_score == d("0.000000")
    assert report.max_freshness_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("agent_reach_retrieval_health_no_inputs",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.research_source_agent_reach_retrieval_health_report_payload(report)
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["input_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_text(payload)
    assert module.validate_research_source_agent_reach_retrieval_health_report_payload(
        payload,
    )


def test_agent_reach_retrieval_health_aggregates_sanitized_health_dimensions() -> None:
    module = api()
    report = build_report(
        input_row("safe-pass"),
        input_row(
            "safe-watch",
            freshness_age_seconds=d("90000.000000"),
            evidence_family_count=d("3.000000"),
            required_evidence_family_count=d("4.000000"),
            source_quorum_count=d("2.000000"),
            required_source_quorum_count=d("3.000000"),
            failed_retrieval_count=d("1.000000"),
        ),
        input_row(
            "safe-block",
            freshness_age_seconds=d("300000.000000"),
            evidence_family_count=d("1.000000"),
            required_evidence_family_count=d("4.000000"),
            source_quorum_count=d("1.000000"),
            required_source_quorum_count=d("3.000000"),
            failed_retrieval_count=d("3.000000"),
        ),
    )

    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.max_freshness_age_seconds == d("300000.000000")
    assert report.total_retrieval_attempt_count == d("12.000000")
    assert report.total_failed_retrieval_count == d("4.000000")
    assert report.failed_retrieval_pressure_ratio == d("0.333333")
    assert report.avg_evidence_diversity_ratio == d("0.666667")
    assert report.avg_source_quorum_ratio == d("0.666667")
    assert report.min_retrieval_health_score == d("0.000000")
    assert report.reason_codes == (
        "freshness_age_above_block_threshold",
        "freshness_age_above_watch_threshold",
        "evidence_diversity_below_block_threshold",
        "source_quorum_below_block_threshold",
        "source_quorum_below_watch_threshold",
        "failed_retrieval_pressure_block",
        "failed_retrieval_pressure_watch",
        "retrieval_health_block",
        "retrieval_health_watch",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.retrieval_ref for row in report.rows) == (
        "redacted-agent-reach-retrieval-000001",
        "redacted-agent-reach-retrieval-000002",
        "redacted-agent-reach-retrieval-000003",
    )
    assert tuple(row.evidence_diversity_ratio for row in report.rows) == (
        d("0.250000"),
        d("0.750000"),
        d("1.000000"),
    )
    assert tuple(row.source_quorum_ratio for row in report.rows) == (
        d("0.333333"),
        d("0.666667"),
        d("1.000000"),
    )
    assert tuple(row.failed_retrieval_pressure_ratio for row in report.rows) == (
        d("0.750000"),
        d("0.250000"),
        d("0.000000"),
    )
    assert report.rows[0].reason_codes == (
        "freshness_age_above_block_threshold",
        "evidence_diversity_below_block_threshold",
        "source_quorum_below_block_threshold",
        "failed_retrieval_pressure_block",
        "retrieval_health_block",
    )
    assert report.rows[1].reason_codes == (
        "freshness_age_above_watch_threshold",
        "source_quorum_below_watch_threshold",
        "failed_retrieval_pressure_watch",
        "retrieval_health_watch",
    )
    assert report.rows[2].reason_codes == ("retrieval_health_pass",)

    payload = module.research_source_agent_reach_retrieval_health_report_payload(report)
    assert payload == module.research_source_agent_reach_retrieval_health_report_payload(
        report,
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["rows"][0]["retrieval_ref"] == (
        "redacted-agent-reach-retrieval-000001"
    )
    assert payload["rows"][0]["source_quorum_ratio"] == "0.333333"
    assert all(
        value != "safe-pass" and value != "safe-watch" and value != "safe-block"
        for value in _walk_payload_values(payload)
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_text(payload)
    assert module.validate_research_source_agent_reach_retrieval_health_report_payload(
        payload,
    )


def test_decimal_only_frozen_exact_types_public_statuses_and_hard_flags() -> None:
    module = api()
    report = build_report(input_row("safe-types"))

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.ResearchSourceAgentReachRetrievalHealthConfig.__dataclass_params__.frozen
    assert module.ResearchSourceAgentReachRetrievalHealthInput.__dataclass_params__.frozen
    assert module.ResearchSourceAgentReachRetrievalHealthRow.__dataclass_params__.frozen
    assert module.ResearchSourceAgentReachRetrievalHealthReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedAgentReachConfig", (module.ResearchSourceAgentReachRetrievalHealthConfig,), {})
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_agent_reach_retrieval_health_report(
            (input_row("safe-time"),),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="watch_freshness_age_seconds"):
        config(watch_freshness_age_seconds=_DecimalSubclass("86400.000000"))
    with pytest.raises(ValueError, match="block_freshness_age_seconds"):
        config(block_freshness_age_seconds=259200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="freshness_age_seconds"):
        input_row("safe-int", freshness_age_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_family_count"):
        input_row("safe-float", evidence_family_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_quorum_count"):
        input_row("safe-subclass", source_quorum_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="failed_retrieval_count"):
        input_row("safe-failed", failed_retrieval_count=d("5.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row("safe-flags", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_payload_rejects_sensitive_public_surfaces_and_digest_tampering() -> None:
    module = api()
    payload = module.research_source_agent_reach_retrieval_health_report_payload(
        build_report(input_row("safe-payload")),
    )

    for unsafe_key in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order_id",
        "trade_id",
        "live_trading_surface",
        "sizing_hint",
        "recommendation",
    ):
        tampered = dict(payload)
        tampered[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="public"):
            module.research_source_agent_reach_retrieval_health_report_payload(tampered)

    for unsafe_value in (
        "raw candidate id abc",
        "https://example.test/source",
        "primary source_url",
        "wallet auth token",
        "order trade surface",
        "sizing recommendation",
    ):
        tampered = dict(payload)
        tampered["operator_note"] = unsafe_value
        with pytest.raises(ValueError, match="public"):
            module.research_source_agent_reach_retrieval_health_report_payload(tampered)

    tampered_digest = dict(payload)
    tampered_digest["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_agent_reach_retrieval_health_report_payload(
            tampered_digest,
        )

    with pytest.raises(ValueError, match="unsafe public"):
        input_row("market_slug_real")
    with pytest.raises(ValueError, match="unsafe public"):
        input_row("https://example.test/retrieval")


def test_module_has_no_network_database_or_trading_runtime_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
