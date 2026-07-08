from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_source_breaking_news_update_pressure_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_breaking_news_update_pressure_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def observation(
    *,
    source_family: str = "official_primary",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    corroborating_update_count: Decimal = d("2.000000"),
    required_corroborating_update_count: Decimal = d("2.000000"),
    contradiction_count: Decimal = d("0.000000"),
    checked_claim_count: Decimal = d("2.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceBreakingNewsUpdatePressureObservation(
        source_family=source_family,
        observed_at=observed_at,
        corroborating_update_count=corroborating_update_count,
        required_corroborating_update_count=required_corroborating_update_count,
        contradiction_count=contradiction_count,
        checked_claim_count=checked_claim_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_source_breaking_news_update_pressure_report(
        observations,
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name == "reason_code_counts":
            continue
        field_value = getattr(value, field.name)
        if isinstance(field_value, bool) or field_value is None:
            continue
        if any(
            marker in field.name
            for marker in (
                "age",
                "count",
                "gap",
                "pressure",
                "ratio",
                "score",
            )
        ):
            assert type(field_value) is Decimal, field.name


def assert_no_json_numbers(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_json_numbers(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_json_numbers(item_value)


def assert_no_raw_public_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "candidate",
        "condition_id",
        "database",
        "dsn",
        "market_id",
        "market_slug",
        "question",
        "raw",
        "recommendation",
        "slug",
        "source_id",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
        "order",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate",
        "database",
        "dsn",
        "market",
        "order",
        "question",
        "raw",
        "token",
        "trade",
        "wallet",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_raw_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_raw_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_empty_report_is_pure_report_only_decimal_digest_bound_and_safe() -> None:
    module = api()
    report = build_report()

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert module.BREAKING_NEWS_UPDATE_PRESSURE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.update_count == d("0.000000")
    assert report.source_family_count == d("0.000000")
    assert report.latest_update_age_seconds == d("0.000000")
    assert report.average_update_age_seconds == d("0.000000")
    assert report.corroboration_gap_ratio == d("0.000000")
    assert report.contradiction_pressure_ratio == d("0.000000")
    assert report.source_family_diversity_ratio == d("0.000000")
    assert report.check_count == d("0.000000")
    assert report.reason_codes == ("breaking_news_update_pressure_no_inputs",)
    assert report.reason_code_counts == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_public_numbers(report)

    payload = report.payload
    digest_value = module.research_source_breaking_news_update_pressure_report_digest(
        report,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "pass"
    assert payload["update_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    assert module.validate_research_source_breaking_news_update_pressure_public_payload(
        payload,
    )
    assert_no_json_numbers(payload)
    assert_no_raw_public_surface(payload)


def test_report_aggregates_update_corroboration_contradiction_and_diversity() -> None:
    report = build_report(
        observation(
            source_family="official_primary",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            corroborating_update_count=d("1.000000"),
            required_corroborating_update_count=d("2.000000"),
            contradiction_count=d("1.000000"),
            checked_claim_count=d("2.000000"),
        ),
        observation(
            source_family="official_primary",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            corroborating_update_count=d("1.000000"),
            required_corroborating_update_count=d("2.000000"),
            contradiction_count=d("1.000000"),
            checked_claim_count=d("2.000000"),
        ),
        observation(
            source_family="wire_service",
            observed_at=GENERATED_AT - timedelta(minutes=10),
            corroborating_update_count=d("2.000000"),
            required_corroborating_update_count=d("2.000000"),
            contradiction_count=d("1.000000"),
            checked_claim_count=d("2.000000"),
        ),
        observation(
            source_family="wire_service",
            observed_at=GENERATED_AT - timedelta(minutes=5),
            corroborating_update_count=d("2.000000"),
            required_corroborating_update_count=d("2.000000"),
            contradiction_count=d("0.000000"),
            checked_claim_count=d("2.000000"),
        ),
    )

    assert report.status == "watch"
    assert report.update_count == d("4.000000")
    assert report.source_family_count == d("2.000000")
    assert report.latest_update_age_seconds == d("300.000000")
    assert report.average_update_age_seconds == d("975.000000")
    assert report.corroborating_update_count == d("6.000000")
    assert report.required_corroborating_update_count == d("8.000000")
    assert report.corroboration_gap_ratio == d("0.250000")
    assert report.contradiction_count == d("3.000000")
    assert report.checked_claim_count == d("8.000000")
    assert report.contradiction_pressure_ratio == d("0.375000")
    assert report.source_family_diversity_ratio == d("0.500000")
    assert report.check_count == d("4.000000")
    assert report.passed_check_count == d("2.000000")
    assert report.watch_check_count == d("2.000000")
    assert report.blocked_check_count == d("0.000000")
    assert report.reason_codes == (
        "update_age_pass",
        "corroboration_gap_pass",
        "contradiction_pressure_watch",
        "source_family_diversity_watch",
    )
    assert tuple(row.reason_code for row in report.reason_code_counts) == (
        "update_age_pass",
        "corroboration_gap_pass",
        "contradiction_pressure_watch",
        "source_family_diversity_watch",
    )
    assert tuple(row.count for row in report.reason_code_counts) == (
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
    )


def test_payload_digest_is_deterministic_validated_and_excludes_inputs() -> None:
    module = api()
    observations = (
        observation(
            source_family="official_primary",
            observed_at=GENERATED_AT - timedelta(hours=3),
            corroborating_update_count=d("0.000000"),
            required_corroborating_update_count=d("4.000000"),
            contradiction_count=d("3.000000"),
            checked_claim_count=d("4.000000"),
        ),
        observation(
            source_family="wire_service",
            observed_at=GENERATED_AT - timedelta(hours=2),
            corroborating_update_count=d("1.000000"),
            required_corroborating_update_count=d("4.000000"),
            contradiction_count=d("2.000000"),
            checked_claim_count=d("4.000000"),
        ),
    )

    first = build_report(*observations)
    second = build_report(*reversed(observations))

    assert first.status == "block"
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_source_breaking_news_update_pressure_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first.payload == second.payload
    assert "official_primary" not in json.dumps(first.payload, sort_keys=True)
    assert "wire_service" not in json.dumps(first.payload, sort_keys=True)
    assert module.validate_research_source_breaking_news_update_pressure_public_payload(
        first.payload,
    )
    assert_no_json_numbers(first.payload)
    assert_no_raw_public_surface(first.payload)

    tampered = dict(first.payload)
    tampered["status"] = "pass"
    assert not module.validate_research_source_breaking_news_update_pressure_public_payload(
        tampered,
    )

    unsafe = dict(first.payload)
    unsafe["source_url"] = "https://example.invalid/raw"
    unsafe["derived_validation_digest"] = first.derived_validation_digest
    assert not module.validate_research_source_breaking_news_update_pressure_public_payload(
        unsafe,
    )


def test_dataclasses_are_frozen_strict_and_do_not_expose_live_surfaces() -> None:
    module = api()
    report = build_report(observation())

    public_classes = (
        module.ResearchSourceBreakingNewsUpdatePressureConfig,
        module.ResearchSourceBreakingNewsUpdatePressureObservation,
        module.ResearchSourceBreakingNewsUpdatePressureReasonCodeCount,
        module.ResearchSourceBreakingNewsUpdatePressureReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourceBreakingNewsUpdatePressureReport):
            pass

    with pytest.raises(ValueError, match="corroborating_update_count must be exactly Decimal"):
        observation(corroborating_update_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="checked_claim_count must be exactly Decimal"):
        observation(checked_claim_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 11, 55))

    with pytest.raises(ValueError, match="unsafe"):
        observation(source_family="https://example.invalid/raw-source")

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(report, status="halt")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, update_count=d("2.000000"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "httpx",
        "psycopg",
        "py_clob_client",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "web3",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    public_names = set(dir(module))
    forbidden_public_names = {
        "auth",
        "client",
        "database",
        "dsn",
        "live",
        "order",
        "recommendation",
        "sizing",
        "table",
        "token",
        "trade",
        "wallet",
    }
    assert public_names.isdisjoint(forbidden_public_names)
