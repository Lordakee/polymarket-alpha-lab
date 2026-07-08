from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.research_source_discovery_coverage_sla_report",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"expected report module to exist: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_source_class_found_watch_ratio": d("1.000000"),
        "min_source_class_found_block_ratio": d("0.500000"),
        "max_missing_class_pressure_watch_ratio": d("0.000000"),
        "max_missing_class_pressure_block_ratio": d("0.500000"),
        "max_discovery_freshness_watch_seconds": d("3600.000000"),
        "max_discovery_freshness_block_seconds": d("7200.000000"),
        "min_parse_quality_ready_watch_ratio": d("0.800000"),
        "min_parse_quality_ready_block_ratio": d("0.600000"),
        "max_retry_backlog_watch_ratio": d("0.250000"),
        "max_retry_backlog_block_ratio": d("0.500000"),
        "max_manual_review_urgency_watch_ratio": d("0.500000"),
        "max_manual_review_urgency_block_ratio": d("0.850000"),
    }
    values.update(overrides)
    return module.ResearchSourceDiscoveryCoverageSlaConfig(**values)


def source_class(
    name: str,
    *,
    required: str = "2.000000",
    discovered: str = "2.000000",
    freshness_age: str = "900.000000",
    parse_ready: str = "2.000000",
    retry_backlog: str = "0.000000",
    review_items: str = "1.000000",
    review_capacity: str = "4.000000",
) -> Any:
    module = api()
    return module.ResearchSourceDiscoveryCoverageSlaInput(
        source_class=name,
        required_source_count=d(required),
        discovered_source_count=d(discovered),
        discovery_freshness_age_seconds=d(freshness_age),
        parse_ready_source_count=d(parse_ready),
        retry_backlog_count=d(retry_backlog),
        manual_review_item_count=d(review_items),
        manual_review_capacity_count=d(review_capacity),
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_discovery_coverage_sla_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_discovery_coverage_sla_empty_input_blocks_without_private_surface() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceDiscoveryCoverageSlaReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.required_source_class_count == d("0.000000")
    assert report.found_source_class_count == d("0.000000")
    assert report.missing_source_class_count == d("0.000000")
    assert report.source_class_found_ratio == d("0.000000")
    assert report.missing_class_pressure_ratio == d("0.000000")
    assert report.coverage_rows == ()
    assert report.reason_codes == (
        "research_source_discovery_coverage_sla_no_source_classes",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_discovery_coverage_sla_aggregates_coverage_freshness_and_queues() -> None:
    report = build_report(
        source_class("official"),
        source_class(
            "corroborating",
            required="4.000000",
            discovered="3.000000",
            freshness_age="4500.000000",
            parse_ready="2.000000",
            retry_backlog="1.000000",
            review_items="4.000000",
            review_capacity="8.000000",
        ),
        source_class(
            "statistical",
            required="2.000000",
            discovered="0.000000",
            freshness_age="9000.000000",
            parse_ready="0.000000",
            retry_backlog="2.000000",
            review_items="9.000000",
            review_capacity="10.000000",
        ),
    )

    assert tuple(row.status for row in report.coverage_rows) == (
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.source_class for row in report.coverage_rows) == (
        "statistical",
        "corroborating",
        "official",
    )
    assert tuple(row.source_class_found for row in report.coverage_rows) == (
        False,
        True,
        True,
    )
    assert tuple(row.missing_source_count for row in report.coverage_rows) == (
        d("2.000000"),
        d("1.000000"),
        d("0.000000"),
    )
    assert tuple(row.parse_quality_ready_ratio for row in report.coverage_rows) == (
        d("0.000000"),
        d("0.666667"),
        d("1.000000"),
    )
    assert tuple(row.retry_backlog_ratio for row in report.coverage_rows) == (
        d("1.000000"),
        d("0.250000"),
        d("0.000000"),
    )
    assert tuple(row.manual_review_urgency_ratio for row in report.coverage_rows) == (
        d("0.900000"),
        d("0.500000"),
        d("0.250000"),
    )
    assert report.status == "block"
    assert report.required_source_class_count == d("3.000000")
    assert report.found_source_class_count == d("2.000000")
    assert report.covered_source_class_count == d("1.000000")
    assert report.missing_source_class_count == d("1.000000")
    assert report.required_source_count == d("8.000000")
    assert report.discovered_source_count == d("5.000000")
    assert report.missing_source_count == d("3.000000")
    assert report.source_class_found_ratio == d("0.666667")
    assert report.source_class_coverage_ratio == d("0.333333")
    assert report.missing_class_pressure_ratio == d("0.333333")
    assert report.discovery_freshness_age_seconds == d("9000.000000")
    assert report.parse_quality_ready_ratio == d("0.800000")
    assert report.retry_backlog_ratio == d("0.375000")
    assert report.manual_review_urgency_ratio == d("0.636364")
    assert report.block_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.reason_codes == (
        "research_source_discovery_coverage_sla_incomplete_class_coverage",
        "research_source_discovery_coverage_sla_missing_source_class",
        "research_source_discovery_coverage_sla_stale_discovery_freshness",
        "research_source_discovery_coverage_sla_parse_quality_not_ready",
        "research_source_discovery_coverage_sla_retry_backlog_pressure",
        "research_source_discovery_coverage_sla_manual_review_urgent",
    )


def test_discovery_coverage_sla_statuses_are_exactly_pass_watch_block() -> None:
    module = api()
    pass_report = build_report(source_class("official"))
    watch_report = build_report(
        source_class(
            "corroborating",
            required="4.000000",
            discovered="3.000000",
            parse_ready="3.000000",
        ),
    )
    block_report = build_report(
        source_class(
            "statistical",
            discovered="0.000000",
            parse_ready="0.000000",
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert pass_report.status == "pass"
    assert pass_report.coverage_rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.coverage_rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.coverage_rows[0].status == "block"


def test_discovery_coverage_sla_rejects_non_decimals_flags_and_leaky_values() -> None:
    module = api()
    report = build_report(source_class("official"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(ValueError, match="min_source_class_found_watch_ratio"):
        config(min_source_class_found_watch_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="required_source_count"):
        source_class("official", required="0.000000")
    with pytest.raises(ValueError, match="parse_ready_source_count"):
        module.ResearchSourceDiscoveryCoverageSlaInput(
            source_class="official",
            required_source_count=d("2.000000"),
            discovered_source_count=d("2.000000"),
            discovery_freshness_age_seconds=d("900.000000"),
            parse_ready_source_count=_DecimalSubclass("2.000000"),
            retry_backlog_count=d("0.000000"),
            manual_review_item_count=d("1.000000"),
            manual_review_capacity_count=d("4.000000"),
        )
    with pytest.raises(ValueError, match="source_class"):
        source_class("market_id_leak")
    with pytest.raises(ValueError, match="source_class"):
        source_class("http_source")
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_discovery_coverage_sla_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_discovery_coverage_sla_payload_is_deterministic_safe_and_digest_checked() -> None:
    module = api()
    rows = (
        source_class(
            "statistical",
            required="2.000000",
            discovered="0.000000",
            freshness_age="9000.000000",
            parse_ready="0.000000",
            retry_backlog="2.000000",
            review_items="9.000000",
            review_capacity="10.000000",
        ),
        source_class("official"),
    )

    payload = module.research_source_discovery_coverage_sla_report_payload(
        build_report(*rows),
    )
    reversed_payload = module.research_source_discovery_coverage_sla_report_payload(
        build_report(*reversed(rows)),
    )
    tampered_payload = dict(payload)
    tampered_payload["status"] = "pass"

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_discovery_coverage_sla_report_payload(payload)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_discovery_coverage_sla_report_payload(
            tampered_payload,
        )
    assert payload["coverage_rows"][0]["source_class"] == "statistical"
    assert payload["coverage_rows"][0]["retry_backlog_ratio"] == "1.000000"
    assert json.dumps(payload, sort_keys=True)
    _assert_public_safe(payload)
    _assert_no_non_decimal_public_numbers(build_report(*rows))


def test_discovery_coverage_sla_exports_only_pure_report_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_DISCOVERY_COVERAGE_SLA_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceDiscoveryCoverageSlaConfig",
        "ResearchSourceDiscoveryCoverageSlaInput",
        "ResearchSourceDiscoveryCoverageSlaReport",
        "ResearchSourceDiscoveryCoverageSlaRow",
        "build_research_source_discovery_coverage_sla_report",
        "research_source_discovery_coverage_sla_report_payload",
        "validate_research_source_discovery_coverage_sla_report_payload",
    )
    for cls in (
        module.ResearchSourceDiscoveryCoverageSlaConfig,
        module.ResearchSourceDiscoveryCoverageSlaInput,
        module.ResearchSourceDiscoveryCoverageSlaReport,
        module.ResearchSourceDiscoveryCoverageSlaRow,
    ):
        assert is_dataclass(cls)
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(
                fragment in lowered
                for fragment in (
                    "raw",
                    "url",
                    "text",
                    "market",
                    "candidate",
                    "dsn",
                    "table",
                    "token",
                    "private",
                    "wallet",
                    "order",
                )
            )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "raw_url",
        "source_url",
        "source_text",
        "market_id",
        "candidate_id",
        "private_token",
        "table_name",
        "dsn",
        "recommendation",
        "sizing",
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "trade",
        "private_key",
        "credential",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _assert_public_safe(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert not any(
                fragment in key.lower()
                for fragment in (
                    "raw",
                    "url",
                    "text",
                    "market",
                    "candidate",
                    "dsn",
                    "table",
                    "token",
                    "private",
                    "wallet",
                    "order",
                )
            )
            _assert_public_safe(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_public_safe(item)
        return
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, str):
        lowered = value.lower()
        assert not value.startswith(("http://", "https://"))
        assert "://" not in lowered
        assert "?" not in lowered
        assert "@" not in lowered


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
