from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_corroboration_gap_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_corroboration_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "source-corroboration-gap-report-v0",
        "required_source_classes": (
            "official_reporting",
            "domain_specialist",
            "independent_archive",
        ),
        "min_coverage_score": d("0.750000"),
        "max_corroboration_age_seconds": d("7200.000000"),
        "watch_recheck_urgency_score": d("0.350000"),
        "block_recheck_urgency_score": d("0.700000"),
        "block_missing_source_class_count": d("2"),
        "contradiction_pressure_weight": d("0.300000"),
        "stale_corroboration_weight": d("0.250000"),
        "coverage_gap_weight": d("0.250000"),
        "independence_gap_weight": d("0.200000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceCorroborationGapReportConfig(**values)


def signal(
    group_id: str = "group-alpha",
    *,
    source_class: str = "official_reporting",
    observed_at: datetime = OBSERVED_AT,
    coverage_score: Decimal = d("0.850000"),
    contradiction_pressure: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceCorroborationSignal(
        corroboration_group_id=group_id,
        source_class=source_class,
        observed_at=observed_at,
        coverage_score=coverage_score,
        contradiction_pressure=contradiction_pressure,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *signals: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
):
    module = api()
    return module.build_research_source_corroboration_gap_report(
        signals,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_code_counts"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "score",
                "pressure",
                "age",
                "urgency",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "raw",
        "url",
        "text",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "dsn",
        "table",
        "wallet",
        "order",
        "network",
        "database",
        "token",
        "auth",
        "secret",
        "private_key",
        "api_key",
        "trade",
        "trading",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate",
        "market_slug",
        "slug",
        "dsn",
        "table",
        "wallet",
        "order",
        "database",
        "token",
        "auth",
        "secret",
        "private_key",
        "api_key",
        "trade",
        "trading",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_empty_input_returns_pass_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == "source-corroboration-gap-report-v0"
    assert empty_report.status == "pass"
    assert empty_report.reason_codes == ("source_corroboration_gap_passed",)
    assert empty_report.group_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.max_recheck_urgency_score == d("0.000000")
    assert empty_report.average_recheck_urgency_score == d("0.000000")
    assert empty_report.reason_code_counts == ()
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_numbers(empty_report)

    payload = module.research_source_corroboration_gap_report_payload(empty_report)
    digest_value = module.research_source_corroboration_gap_report_digest(empty_report)
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["status"] == "pass"
    assert payload["group_count"] == "0"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    assert module.research_source_corroboration_gap_report_digest(empty_report) == digest_value


def test_report_scores_missing_stale_contradiction_coverage_and_recheck_gaps() -> None:
    queued = report(
        signal(
            "group-pass",
            source_class="official_reporting",
            coverage_score=d("0.950000"),
            contradiction_pressure=d("0.050000"),
        ),
        signal(
            "group-pass",
            source_class="domain_specialist",
            coverage_score=d("0.900000"),
            contradiction_pressure=d("0.100000"),
        ),
        signal(
            "group-pass",
            source_class="independent_archive",
            coverage_score=d("0.850000"),
            contradiction_pressure=d("0.080000"),
        ),
        signal(
            "group-watch",
            source_class="official_reporting",
            coverage_score=d("0.900000"),
            contradiction_pressure=d("0.200000"),
        ),
        signal(
            "group-watch",
            source_class="domain_specialist",
            coverage_score=d("0.800000"),
            contradiction_pressure=d("0.150000"),
        ),
        signal(
            "group-block",
            source_class="official_reporting",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            coverage_score=d("0.400000"),
            contradiction_pressure=d("0.900000"),
        ),
    )

    assert queued.status == "block"
    assert queued.group_count == d("3")
    assert queued.pass_count == d("1")
    assert queued.watch_count == d("1")
    assert queued.block_count == d("1")
    assert tuple(row.corroboration_group_id for row in queued.rows) == (
        "group-block",
        "group-watch",
        "group-pass",
    )

    blocked, watched, passed = queued.rows
    assert blocked.status == "block"
    assert blocked.source_class_count == d("1")
    assert blocked.missing_source_class_count == d("2")
    assert blocked.stale_corroboration_count == d("1")
    assert blocked.coverage_gap_count == d("1")
    assert blocked.max_source_age_seconds == d("9000.000000")
    assert blocked.average_coverage_score == d("0.400000")
    assert blocked.max_contradiction_pressure == d("0.900000")
    assert blocked.recheck_urgency_score == d("0.903333")
    assert blocked.reason_codes == (
        "contradiction_pressure_block",
        "coverage_gap_block",
        "missing_independent_source_classes_block",
        "recheck_urgency_block",
        "stale_corroboration_block",
        "source_corroboration_gap_block",
    )

    assert watched.status == "watch"
    assert watched.source_class_count == d("2")
    assert watched.missing_source_class_count == d("1")
    assert watched.stale_corroboration_count == d("0")
    assert watched.coverage_gap_count == d("0")
    assert watched.max_contradiction_pressure == d("0.200000")
    assert watched.recheck_urgency_score == d("0.126667")
    assert watched.reason_codes == (
        "missing_independent_source_classes_watch",
        "source_corroboration_gap_watch",
    )

    assert passed.status == "pass"
    assert passed.source_class_count == d("3")
    assert passed.missing_source_class_count == d("0")
    assert passed.max_source_age_seconds == d("1800.000000")
    assert passed.average_coverage_score == d("0.900000")
    assert passed.recheck_urgency_score == d("0.030000")
    assert passed.reason_codes == ("source_corroboration_gap_passed",)


def test_payload_is_decimal_string_json_ready_sanitized_and_deterministic() -> None:
    module = api()
    signals = (
        signal("group-alpha", source_class="official_reporting"),
        signal("group-alpha", source_class="domain_specialist"),
        signal("group-alpha", source_class="independent_archive"),
        signal(
            "group-beta",
            source_class="official_reporting",
            coverage_score=d("0.500000"),
            contradiction_pressure=d("0.700000"),
        ),
    )
    first = report(*signals)
    second = report(*reversed(signals))

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["group_count"] == "2"
    assert payload["rows"][0]["corroboration_group_id"] == "group-beta"
    assert payload["rows"][0]["coverage_gap_count"] == "1"
    assert payload["rows"][0]["max_contradiction_pressure"] == "0.700000"
    assert payload["rows"][1]["average_coverage_score"] == "0.850000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_source_corroboration_gap_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_numbers(first)


def test_dataclasses_are_frozen_and_reject_subclassing_and_bad_flags() -> None:
    module = api()
    built = report(
        signal("group-alpha", source_class="official_reporting"),
        signal("group-alpha", source_class="domain_specialist"),
        signal("group-alpha", source_class="independent_archive"),
    )

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchSourceCorroborationGapReportConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)


def test_strict_types_unsafe_inputs_and_live_surfaces_are_rejected() -> None:
    with pytest.raises(ValueError, match="coverage_score must be a Decimal"):
        signal(coverage_score=0.8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="contradiction_pressure must be exactly Decimal"):
        signal(contradiction_pressure=_DecimalSubclass("0.800000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only must be a bool"):
        signal(paper_only=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        signal(observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="unsafe"):
        signal(source_class="https://example.invalid/source")

    with pytest.raises(ValueError, match="unsafe"):
        signal("candidate_id_123")

    with pytest.raises(ValueError, match="unsafe"):
        signal("market_slug_alpha")

    with pytest.raises(ValueError, match="unsafe"):
        signal("postgres_dsn_alias")

    with pytest.raises(ValueError, match="unsafe"):
        signal("positions_table")

    with pytest.raises(ValueError, match="required_source_classes must be non-empty"):
        cfg(required_source_classes=())

    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(independence_gap_weight=d("0.100000"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    public_names = set(dir(api()))
    assert "client" not in public_names
    assert "wallet" not in public_names
    assert "order" not in public_names
