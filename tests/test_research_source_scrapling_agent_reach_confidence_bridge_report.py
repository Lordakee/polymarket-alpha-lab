from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_scrapling_agent_reach_confidence_bridge_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    private_bridge_ref: str = (
        "raw_candidate_id=secret-candidate|market_id=secret-market|"
        "market_slug=secret-slug|question=private question|"
        "source_url=https://example.invalid/path?token=secret&wallet=secret"
    ),
    observed_seconds_ago: int = 300,
    scrapling_capture_confidence_score: Decimal = d("0.920000"),
    scrapling_extraction_confidence_score: Decimal = d("0.880000"),
    agent_reach_retrieval_confidence_score: Decimal = d("0.900000"),
    agent_reach_corroboration_confidence_score: Decimal = d("0.860000"),
    authority_alignment_score: Decimal = d("0.870000"),
    freshness_score: Decimal = d("0.950000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    unresolved_gap_score: Decimal = d("0.040000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraplingAgentReachConfidenceBridgeObservation(
        private_bridge_ref=private_bridge_ref,
        observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        scrapling_capture_confidence_score=scrapling_capture_confidence_score,
        scrapling_extraction_confidence_score=scrapling_extraction_confidence_score,
        agent_reach_retrieval_confidence_score=agent_reach_retrieval_confidence_score,
        agent_reach_corroboration_confidence_score=agent_reach_corroboration_confidence_score,
        authority_alignment_score=authority_alignment_score,
        freshness_score=freshness_score,
        contradiction_pressure_score=contradiction_pressure_score,
        unresolved_gap_score=unresolved_gap_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_scrapling_agent_reach_confidence_bridge_report(
        rows,
        config=cfg,
        generated_at=GENERATED_AT,
    )


def test_pass_report_redacts_private_inputs_and_exports_stable_digest_payload() -> None:
    module = api()
    report_a = build_report(
        observation(private_bridge_ref="private-alpha"),
        observation(
            private_bridge_ref=(
                "raw_candidate_id=secret-two|source_text=verbatim private text"
            ),
            observed_seconds_ago=600,
            scrapling_capture_confidence_score=d("0.940000"),
            scrapling_extraction_confidence_score=d("0.900000"),
            agent_reach_retrieval_confidence_score=d("0.910000"),
            agent_reach_corroboration_confidence_score=d("0.890000"),
        ),
    )
    report_b = build_report(
        observation(
            private_bridge_ref="changed-private-two",
            observed_seconds_ago=600,
            scrapling_capture_confidence_score=d("0.940000"),
            scrapling_extraction_confidence_score=d("0.900000"),
            agent_reach_retrieval_confidence_score=d("0.910000"),
            agent_reach_corroboration_confidence_score=d("0.890000"),
        ),
        observation(private_bridge_ref="changed-private-one"),
    )
    changed_report = build_report(
        observation(scrapling_capture_confidence_score=d("0.700000")),
    )

    assert type(report_a) is module.ResearchSourceScraplingAgentReachConfidenceBridgeReport
    assert is_dataclass(report_a)
    assert report_a.status == "pass"
    assert report_a.observation_count == d("2.000000")
    assert report_a.pass_count == d("2.000000")
    assert report_a.watch_count == d("0.000000")
    assert report_a.block_count == d("0.000000")
    assert report_a.average_bridge_confidence_score == d("0.907500")
    assert report_a.highest_confidence_gap_ratio == d("0.020000")
    assert report_a.reason_codes == (
        "scrapling_agent_reach_confidence_bridge_pass",
    )
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.derived_validation_digest != changed_report.derived_validation_digest

    payload = report_a.payload
    assert payload == module.research_source_scrapling_agent_reach_confidence_bridge_report_payload(
        report_a,
    )
    assert payload["derived_validation_digest"] == module.research_source_scrapling_agent_reach_confidence_bridge_report_digest(
        report_a,
    )
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["row_index"] == "1.000000"
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    json.dumps(payload, sort_keys=True)
    assert module.validate_research_source_scrapling_agent_reach_confidence_bridge_report_payload(
        payload,
    )
    assert_no_decimal_or_float_values(payload)
    assert_payload_has_no_forbidden_values(payload)


def test_watch_and_block_statuses_use_only_pass_watch_block_reason_order() -> None:
    watch_report = build_report(
        observation(
            scrapling_capture_confidence_score=d("0.700000"),
            scrapling_extraction_confidence_score=d("0.700000"),
            agent_reach_retrieval_confidence_score=d("0.620000"),
            agent_reach_corroboration_confidence_score=d("0.620000"),
            authority_alignment_score=d("0.720000"),
            freshness_score=d("0.700000"),
            contradiction_pressure_score=d("0.200000"),
            unresolved_gap_score=d("0.150000"),
        ),
    )
    block_report = build_report(
        observation(
            scrapling_capture_confidence_score=d("0.900000"),
            scrapling_extraction_confidence_score=d("0.900000"),
            agent_reach_retrieval_confidence_score=d("0.250000"),
            agent_reach_corroboration_confidence_score=d("0.250000"),
            authority_alignment_score=d("0.400000"),
            freshness_score=d("0.400000"),
            contradiction_pressure_score=d("0.500000"),
            unresolved_gap_score=d("0.400000"),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert watch_report.rows[0].reason_codes == (
        "bridge_confidence_below_pass_threshold",
        "dual_tool_floor_below_pass_threshold",
        "contradiction_pressure_above_pass_threshold",
        "unresolved_gap_above_pass_threshold",
    )
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"
    assert block_report.rows[0].reason_codes == (
        "bridge_confidence_below_watch_threshold",
        "dual_tool_floor_below_watch_threshold",
        "confidence_gap_above_watch_threshold",
        "contradiction_pressure_above_watch_threshold",
        "unresolved_gap_above_watch_threshold",
    )
    assert {watch_report.status, block_report.status, "pass"} == {
        "pass",
        "watch",
        "block",
    }


def test_empty_report_blocks_with_decimal_zeroes_and_frozen_report_only_flags() -> None:
    module = api()
    report = build_report()

    assert module.RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_CONFIDENCE_BRIDGE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.observation_count == d("0.000000")
    assert report.average_bridge_confidence_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "scrapling_agent_reach_confidence_bridge_no_inputs",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.derived_validation_digest == module.research_source_scrapling_agent_reach_confidence_bridge_report_digest(
        report,
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourceScraplingAgentReachConfidenceBridgeReport):
            pass


def test_validation_rejects_non_decimal_future_dates_flags_digest_and_unsafe_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        observation(scrapling_capture_confidence_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(authority_alignment_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(observation(observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_scrapling_agent_reach_confidence_bridge_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    broken_payload = dict(report.payload)
    broken_payload["average_bridge_confidence_score"] = "0.100000"
    assert not module.validate_research_source_scrapling_agent_reach_confidence_bridge_report_payload(
        broken_payload,
    )
    unsafe_payload = dict(report.payload)
    unsafe_payload["source_url"] = "https://example.invalid/private"
    assert not module.validate_research_source_scrapling_agent_reach_confidence_bridge_report_payload(
        unsafe_payload,
    )


def test_payload_validation_rejects_resigned_schema_and_consistency_tampering() -> None:
    module = api()
    report = build_report(observation())

    extra_field_payload = dict(report.payload)
    extra_field_payload["safe_extra"] = "unexpected"
    resign_payload(extra_field_payload)

    inconsistent_payload = dict(report.payload)
    inconsistent_payload["row_count"] = "2.000000"
    resign_payload(inconsistent_payload)

    nested_extra_payload = json.loads(json.dumps(report.payload))
    nested_extra_payload["rows"][0]["safe_extra"] = "unexpected"
    resign_payload(nested_extra_payload)

    for payload in (
        extra_field_payload,
        inconsistent_payload,
        nested_extra_payload,
    ):
        assert not module.validate_research_source_scrapling_agent_reach_confidence_bridge_report_payload(
            payload,
        )


def test_direct_row_validation_rejects_derived_metric_tampering() -> None:
    report = build_report(observation())

    with pytest.raises(ValueError, match="confidence_gap_ratio"):
        replace(
            report.rows[0],
            confidence_gap_ratio=d("0.500000"),
            status="block",
            reason_codes=("confidence_gap_above_watch_threshold",),
        )


def test_direct_report_validation_rejects_noncanonical_or_future_rows() -> None:
    report = build_report(
        observation(observed_seconds_ago=300),
        observation(
            observed_seconds_ago=600,
            scrapling_capture_confidence_score=d("0.940000"),
            scrapling_extraction_confidence_score=d("0.900000"),
        ),
    )

    with pytest.raises(ValueError, match="canonical order"):
        replace(
            report,
            rows=tuple(reversed(report.rows)),
            derived_validation_digest="",
        )

    with pytest.raises(ValueError, match="observed_at"):
        replace(
            report,
            rows=(
                replace(
                    report.rows[0],
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
                report.rows[1],
            ),
            derived_validation_digest="",
        )


def test_module_scope_has_no_network_database_wallet_order_or_trade_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "send",
        "trade",
        "order",
        "recommend",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_calls

    forbidden_import_fragments = (
        "db",
        "http",
        "psycopg",
        "requests",
        "socket",
        "sql",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    forbidden_public_names = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_trade",
        "position_sizing",
        "recommendation",
    }
    public_field_names = {
        field.name
        for cls in (
            module.ResearchSourceScraplingAgentReachConfidenceBridgeConfig,
            module.ResearchSourceScraplingAgentReachConfidenceBridgeRow,
            module.ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount,
            module.ResearchSourceScraplingAgentReachConfidenceBridgeReport,
        )
        for field in fields(cls)
    }
    assert forbidden_public_names.isdisjoint(public_field_names)


def assert_no_decimal_or_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_decimal_or_float_values(item)
    else:
        assert type(value) is not Decimal
        assert type(value) is not float


def assert_payload_has_no_forbidden_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "verbatim private",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
        "private-alpha",
        "changed-private",
        "secret",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_forbidden_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_forbidden_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)


def resign_payload(payload: dict[str, Any]) -> None:
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    canonical_payload = json.dumps(
        values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload["derived_validation_digest"] = sha256(
        canonical_payload.encode("utf-8"),
    ).hexdigest()
