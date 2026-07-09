from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_event_resolution_source_authority_latency_floor_report"
)
GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    private_resolution_ref: str = (
        "raw_candidate_id=secret-candidate|market_id=secret-market|"
        "market_slug=secret-slug|question=private question|"
        "source_url=https://example.invalid/path?token=secret&wallet=secret"
    ),
    observed_seconds_ago: int = 300,
    source_latency_seconds: Decimal = d("300.000000"),
    authority_latency_seconds: Decimal = d("600.000000"),
    source_authority_score: Decimal = d("0.920000"),
    resolution_confidence_score: Decimal = d("0.950000"),
    authority_recheck_score: Decimal = d("0.930000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventResolutionSourceAuthorityLatencyFloorObservation(
        private_resolution_ref=private_resolution_ref,
        observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        source_latency_seconds=source_latency_seconds,
        authority_latency_seconds=authority_latency_seconds,
        source_authority_score=source_authority_score,
        resolution_confidence_score=resolution_confidence_score,
        authority_recheck_score=authority_recheck_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_resolution_source_authority_latency_floor_report(
        rows,
        config=cfg,
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_pass_report_redacts_private_inputs_and_exports_stable_digest_payload() -> None:
    module = api()
    report_a = build_report(
        observation(private_resolution_ref="private-alpha"),
        observation(
            private_resolution_ref=(
                "raw_candidate_id=secret-two|source_text=verbatim private text"
            ),
            observed_seconds_ago=600,
            source_latency_seconds=d("600.000000"),
            authority_latency_seconds=d("900.000000"),
            source_authority_score=d("0.940000"),
            resolution_confidence_score=d("0.960000"),
            authority_recheck_score=d("0.950000"),
        ),
    )
    report_b = build_report(
        observation(
            private_resolution_ref="changed-private-two",
            observed_seconds_ago=600,
            source_latency_seconds=d("600.000000"),
            authority_latency_seconds=d("900.000000"),
            source_authority_score=d("0.940000"),
            resolution_confidence_score=d("0.960000"),
            authority_recheck_score=d("0.950000"),
        ),
        observation(private_resolution_ref="changed-private-one"),
    )
    changed_report = build_report(
        observation(source_latency_seconds=d("1800.000000")),
    )

    assert type(report_a) is module.ResearchEventResolutionSourceAuthorityLatencyFloorReport
    assert is_dataclass(report_a)
    assert report_a.__dataclass_params__.frozen
    assert report_a.status == "pass"
    assert report_a.observation_count == d("2.000000")
    assert report_a.pass_count == d("2.000000")
    assert report_a.watch_count == d("0.000000")
    assert report_a.block_count == d("0.000000")
    assert report_a.average_source_latency_seconds == d("450.000000")
    assert report_a.average_authority_latency_seconds == d("750.000000")
    assert report_a.highest_latency_gap_seconds == d("300.000000")
    assert report_a.average_source_authority_latency_floor_score == d("0.943083")
    assert report_a.reason_codes == (
        "event_resolution_source_authority_latency_floor_pass",
    )
    assert tuple(
        (reason_count.reason_code, reason_count.count)
        for reason_count in report_a.reason_code_counts
    ) == (("event_resolution_source_authority_latency_floor_pass", d("2.000000")),)
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.derived_validation_digest != changed_report.derived_validation_digest

    payload = report_a.payload
    assert payload == module.research_event_resolution_source_authority_latency_floor_report_payload(
        report_a,
    )
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["derived_validation_digest"] == module.research_event_resolution_source_authority_latency_floor_report_digest(
        report_a,
    )
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["row_index"] == "1.000000"
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    json.dumps(payload, sort_keys=True)
    assert module.validate_research_event_resolution_source_authority_latency_floor_report_payload(
        payload,
    )
    assert_no_decimal_or_float_values(payload)
    assert_payload_has_no_forbidden_values(payload)


def test_watch_and_block_statuses_use_only_pass_watch_block_reason_order() -> None:
    watch_report = build_report(
        observation(
            source_latency_seconds=d("1500.000000"),
            authority_latency_seconds=d("2000.000000"),
            source_authority_score=d("0.700000"),
            resolution_confidence_score=d("0.700000"),
            authority_recheck_score=d("0.700000"),
        ),
    )
    block_report = build_report(
        observation(
            source_latency_seconds=d("4000.000000"),
            authority_latency_seconds=d("8000.000000"),
            source_authority_score=d("0.200000"),
            resolution_confidence_score=d("0.200000"),
            authority_recheck_score=d("0.200000"),
        ),
    )

    assert module_statuses() == ("pass", "watch", "block")
    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert watch_report.rows[0].reason_codes == (
        "source_authority_latency_floor_score_below_pass_threshold",
        "source_latency_above_pass_threshold",
        "authority_latency_above_pass_threshold",
    )
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"
    assert block_report.rows[0].reason_codes == (
        "source_authority_latency_floor_score_below_watch_threshold",
        "source_latency_above_watch_threshold",
        "authority_latency_above_watch_threshold",
        "latency_gap_above_watch_threshold",
    )
    assert {watch_report.status, block_report.status, "pass"} == {
        "pass",
        "watch",
        "block",
    }


def test_empty_report_blocks_with_decimal_zeroes_and_frozen_report_only_flags() -> None:
    module = api()
    report = build_report()

    assert module_statuses() == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.observation_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.average_source_latency_seconds == d("0.000000")
    assert report.average_authority_latency_seconds == d("0.000000")
    assert report.average_source_authority_latency_floor_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "event_resolution_source_authority_latency_floor_no_inputs",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.derived_validation_digest == module.research_event_resolution_source_authority_latency_floor_report_digest(
        report,
    )
    assert_decimal_public_numbers(report)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(TypeError):

        class BadReport(module.ResearchEventResolutionSourceAuthorityLatencyFloorReport):
            pass


def test_validation_rejects_non_decimal_future_dates_flags_digest_and_unsafe_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        observation(source_latency_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(authority_latency_seconds=_DecimalSubclass("600.000000"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(observation(observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_source_authority_latency_floor_report(
            (),
            generated_at=datetime(2026, 7, 9, 15, 0),
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
    broken_payload["average_source_authority_latency_floor_score"] = "0.100000"
    assert not module.validate_research_event_resolution_source_authority_latency_floor_report_payload(
        broken_payload,
    )
    unsafe_payload = dict(report.payload)
    unsafe_payload["source_url"] = "https://example.invalid/private"
    assert not module.validate_research_event_resolution_source_authority_latency_floor_report_payload(
        unsafe_payload,
    )
    invalid_status_payload = dict(report.payload)
    invalid_status_payload["status"] = "ready"
    invalid_status_payload["derived_validation_digest"] = canonical_digest(
        invalid_status_payload,
    )
    assert not module.validate_research_event_resolution_source_authority_latency_floor_report_payload(
        invalid_status_payload,
    )
    downgraded_flag_payload = dict(report.payload)
    downgraded_flag_payload["readonly"] = False
    downgraded_flag_payload["derived_validation_digest"] = canonical_digest(
        downgraded_flag_payload,
    )
    assert not module.validate_research_event_resolution_source_authority_latency_floor_report_payload(
        downgraded_flag_payload,
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
        "size",
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
            module.ResearchEventResolutionSourceAuthorityLatencyFloorConfig,
            module.ResearchEventResolutionSourceAuthorityLatencyFloorRow,
            module.ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount,
            module.ResearchEventResolutionSourceAuthorityLatencyFloorReport,
        )
        for field in fields(cls)
    }
    assert forbidden_public_names.isdisjoint(public_field_names)


def module_statuses() -> tuple[str, str, str]:
    module = api()
    return module.RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_STATUSES


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


def assert_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric was not Decimal: {value!r}")
    if type(value) is tuple:
        for item in value:
            assert_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_decimal_public_numbers(getattr(value, field.name))


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
