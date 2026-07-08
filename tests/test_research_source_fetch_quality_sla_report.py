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
            "polymarket_alpha_lab.research_source_fetch_quality_sla_report",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"expected report module to exist: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_fetch_success_watch_ratio": d("0.900000"),
        "min_fetch_success_block_ratio": d("0.700000"),
        "max_freshness_age_watch_seconds": d("3600.000000"),
        "max_freshness_age_block_seconds": d("7200.000000"),
        "min_parse_quality_watch_score": d("0.800000"),
        "min_parse_quality_block_score": d("0.600000"),
        "min_corroboration_readiness_watch_ratio": d("0.750000"),
        "min_corroboration_readiness_block_ratio": d("0.500000"),
        "max_retry_pressure_watch_ratio": d("0.200000"),
        "max_retry_pressure_block_ratio": d("0.500000"),
        "max_manual_review_urgency_watch_ratio": d("0.500000"),
        "max_manual_review_urgency_block_ratio": d("0.850000"),
    }
    values.update(overrides)
    return module.ResearchSourceFetchQualitySlaConfig(**values)


def input_row(
    team_id: str,
    category_id: str,
    fetch_batch_id: str,
    *,
    attempted_fetch_count: Decimal = d("10.000000"),
    successful_fetch_count: Decimal = d("10.000000"),
    freshness_age_seconds: Decimal = d("900.000000"),
    parse_quality_score: Decimal = d("0.950000"),
    corroborated_claim_count: Decimal = d("4.000000"),
    required_corroborated_claim_count: Decimal = d("4.000000"),
    retry_attempt_count: Decimal = d("0.000000"),
    manual_review_item_count: Decimal = d("1.000000"),
    manual_review_capacity_count: Decimal = d("4.000000"),
) -> Any:
    module = api()
    return module.ResearchSourceFetchQualitySlaInput(
        team_id=team_id,
        category_id=category_id,
        fetch_batch_id=fetch_batch_id,
        attempted_fetch_count=attempted_fetch_count,
        successful_fetch_count=successful_fetch_count,
        freshness_age_seconds=freshness_age_seconds,
        parse_quality_score=parse_quality_score,
        corroborated_claim_count=corroborated_claim_count,
        required_corroborated_claim_count=required_corroborated_claim_count,
        retry_attempt_count=retry_attempt_count,
        manual_review_item_count=manual_review_item_count,
        manual_review_capacity_count=manual_review_capacity_count,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_fetch_quality_sla_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_fetch_quality_sla_empty_report_is_pass_readonly_and_public() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceFetchQualitySlaReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.batch_count == d("0.000000")
    assert report.attempted_fetch_count == d("0.000000")
    assert report.fetch_success_ratio == d("0.000000")
    assert report.quality_rows == ()
    assert report.reason_codes == (
        "research_source_fetch_quality_sla_no_fetch_batches",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_fetch_quality_sla_aggregates_metrics_and_orders_rows() -> None:
    report = build_report(
        input_row("sports_soccer", "sports.soccer", "sports_batch"),
        input_row(
            "macro_rates",
            "finance.macro.rates",
            "rates_batch",
            freshness_age_seconds=d("4500.000000"),
            parse_quality_score=d("0.750000"),
            corroborated_claim_count=d("6.000000"),
            required_corroborated_claim_count=d("8.000000"),
            retry_attempt_count=d("2.000000"),
            manual_review_item_count=d("5.000000"),
            manual_review_capacity_count=d("10.000000"),
        ),
        input_row(
            "politics",
            "politics",
            "election_batch",
            attempted_fetch_count=d("10.000000"),
            successful_fetch_count=d("6.000000"),
            freshness_age_seconds=d("9000.000000"),
            parse_quality_score=d("0.500000"),
            corroborated_claim_count=d("2.000000"),
            required_corroborated_claim_count=d("6.000000"),
            retry_attempt_count=d("7.000000"),
            manual_review_item_count=d("9.000000"),
            manual_review_capacity_count=d("10.000000"),
        ),
    )

    assert tuple(row.status for row in report.quality_rows) == (
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.fetch_batch_id for row in report.quality_rows) == (
        "election_batch",
        "rates_batch",
        "sports_batch",
    )
    assert tuple(row.fetch_success_ratio for row in report.quality_rows) == (
        d("0.600000"),
        d("1.000000"),
        d("1.000000"),
    )
    assert tuple(row.corroboration_readiness_ratio for row in report.quality_rows) == (
        d("0.333333"),
        d("0.750000"),
        d("1.000000"),
    )
    assert tuple(row.retry_pressure_ratio for row in report.quality_rows) == (
        d("0.700000"),
        d("0.200000"),
        d("0.000000"),
    )
    assert tuple(row.manual_review_urgency_ratio for row in report.quality_rows) == (
        d("0.900000"),
        d("0.500000"),
        d("0.250000"),
    )
    assert report.status == "block"
    assert report.batch_count == d("3.000000")
    assert report.attempted_fetch_count == d("30.000000")
    assert report.successful_fetch_count == d("26.000000")
    assert report.fetch_success_ratio == d("0.866667")
    assert report.max_freshness_age_seconds == d("9000.000000")
    assert report.min_parse_quality_score == d("0.500000")
    assert report.min_corroboration_readiness_ratio == d("0.333333")
    assert report.retry_pressure_ratio == d("0.300000")
    assert report.manual_review_urgency_ratio == d("0.625000")
    assert report.block_batch_count == d("1.000000")
    assert report.watch_batch_count == d("1.000000")
    assert report.reason_codes == (
        "research_source_fetch_quality_sla_low_fetch_success",
        "research_source_fetch_quality_sla_stale_freshness_age",
        "research_source_fetch_quality_sla_low_parse_quality",
        "research_source_fetch_quality_sla_corroboration_not_ready",
        "research_source_fetch_quality_sla_retry_pressure",
        "research_source_fetch_quality_sla_manual_review_urgent",
    )


def test_fetch_quality_sla_statuses_are_exactly_pass_watch_block() -> None:
    module = api()
    pass_report = build_report(input_row("sports_soccer", "sports.soccer", "sports_batch"))
    watch_report = build_report(
        input_row(
            "macro_rates",
            "finance.macro.rates",
            "rates_batch",
            freshness_age_seconds=d("3600.000000"),
        ),
    )
    block_report = build_report(
        input_row(
            "politics",
            "politics",
            "election_batch",
            parse_quality_score=d("0.500000"),
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert pass_report.status == "pass"
    assert pass_report.quality_rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.quality_rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.quality_rows[0].status == "block"


def test_fetch_quality_sla_rejects_non_decimal_values_and_flag_downgrades() -> None:
    module = api()
    report = build_report(input_row("politics", "politics", "election_batch"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"

    with pytest.raises(ValueError, match="min_fetch_success_watch_ratio must be a Decimal"):
        config(min_fetch_success_watch_ratio=1)
    with pytest.raises(ValueError, match="parse_quality_score must be a Decimal"):
        input_row(
            "politics",
            "politics",
            "election_batch",
            parse_quality_score=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="attempted_fetch_count must be a Decimal"):
        input_row(
            "politics",
            "politics",
            "election_batch",
            attempted_fetch_count=10,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_fetch_quality_sla_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_fetch_quality_sla_payload_is_deterministic_safe_and_digest_verified() -> None:
    module = api()
    rows = (
        input_row(
            "politics",
            "politics",
            "election_batch",
            attempted_fetch_count=d("10.000000"),
            successful_fetch_count=d("6.000000"),
            freshness_age_seconds=d("9000.000000"),
            parse_quality_score=d("0.500000"),
            corroborated_claim_count=d("2.000000"),
            required_corroborated_claim_count=d("6.000000"),
            retry_attempt_count=d("7.000000"),
            manual_review_item_count=d("9.000000"),
            manual_review_capacity_count=d("10.000000"),
        ),
        input_row("sports_soccer", "sports.soccer", "sports_batch"),
    )

    payload = module.research_source_fetch_quality_sla_report_payload(build_report(*rows))
    reversed_payload = module.research_source_fetch_quality_sla_report_payload(
        build_report(*reversed(rows)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["quality_rows"][0]["fetch_success_ratio"] == "0.600000"
    assert payload["quality_rows"][0]["retry_pressure_ratio"] == "0.700000"
    assert json.dumps(payload, sort_keys=True)
    _assert_public_safe(payload)
    _assert_no_non_decimal_public_numbers(build_report(*rows))


def test_fetch_quality_sla_exports_only_pure_report_only_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_FETCH_QUALITY_SLA_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceFetchQualitySlaConfig",
        "ResearchSourceFetchQualitySlaInput",
        "ResearchSourceFetchQualitySlaReport",
        "ResearchSourceFetchQualitySlaRow",
        "build_research_source_fetch_quality_sla_report",
        "research_source_fetch_quality_sla_report_payload",
    )
    for cls in (
        module.ResearchSourceFetchQualitySlaConfig,
        module.ResearchSourceFetchQualitySlaInput,
        module.ResearchSourceFetchQualitySlaReport,
        module.ResearchSourceFetchQualitySlaRow,
    ):
        assert is_dataclass(cls)
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(
                fragment in lowered
                for fragment in ("raw", "url", "text", "wallet", "order")
            )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "raw_url",
        "source_text",
        "source_url",
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
                for fragment in ("raw", "url", "text", "wallet", "order")
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
        assert not value.startswith(("http://", "https://"))


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
