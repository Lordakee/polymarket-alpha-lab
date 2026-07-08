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


MODULE_NAME = "polymarket_alpha_lab.research_source_scrapling_capture_health_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scrapling_capture_health_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
CAPTURED_AT = datetime(2026, 7, 8, 11, 45, tzinfo=UTC)
PUBLIC_STATUSES = {"pass", "watch", "block"}


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
        "config_version": "research-source-scrapling-capture-health-report-v0",
        "fresh_capture_max_age_seconds": d("1800.000000"),
        "stale_capture_block_age_seconds": d("7200.000000"),
        "min_fresh_capture_pass_ratio": d("0.800000"),
        "min_fresh_capture_block_ratio": d("0.500000"),
        "min_parse_completeness_pass_ratio": d("0.900000"),
        "min_parse_completeness_block_ratio": d("0.600000"),
        "max_antibot_fallback_pass_ratio": d("0.100000"),
        "max_antibot_fallback_block_ratio": d("0.400000"),
        "min_source_family_pass_count": d("3"),
        "min_source_family_block_count": d("2"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraplingCaptureHealthConfig(**values)


def observation(
    source_family: str = "official-agency",
    *,
    captured_at: datetime = CAPTURED_AT,
    captured_field_count: Decimal = d("9"),
    expected_field_count: Decimal = d("10"),
    capture_attempt_count: Decimal = d("1"),
    antibot_fallback_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceScraplingCaptureObservation(
        source_family=source_family,
        captured_at=captured_at,
        captured_field_count=captured_field_count,
        expected_field_count=expected_field_count,
        capture_attempt_count=capture_attempt_count,
        antibot_fallback_count=antibot_fallback_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
):
    module = api()
    return module.build_research_source_scrapling_capture_health_report(
        observations,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (float, int):
        raise AssertionError(f"public numeric was not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            assert_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_decimal_public_numbers(getattr(value, field.name))


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
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "network",
        "database",
        "authentication",
        "authorization",
        "auth",
        "private_key",
        "api_key",
        "recommendation",
        "sizing",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate",
        "market-id",
        "market_slug",
        "question",
        "wallet",
        "order",
        "trade",
        "database",
        "token",
        "recommendation",
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


def assert_public_status_values(value: Any) -> None:
    if isinstance(value, dict):
        for key, item_value in value.items():
            if key.endswith("status"):
                assert item_value in PUBLIC_STATUSES
            assert_public_status_values(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_public_status_values(item_value)


def test_empty_input_blocks_with_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.__dataclass_params__.frozen
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == (
        "research-source-scrapling-capture-health-report-v0"
    )
    assert empty_report.status == "block"
    assert empty_report.next_step == "block_report_only_scrapling_capture_review"
    assert empty_report.reason_codes == (
        "scrapling_capture_health_no_inputs",
        "scrapling_capture_health_block",
    )
    assert empty_report.input_count == d("0")
    assert empty_report.fresh_capture_count == d("0")
    assert empty_report.stale_capture_count == d("0")
    assert empty_report.source_family_count == d("0")
    assert empty_report.capture_freshness_ratio == d("0.000000")
    assert empty_report.parse_completeness_ratio == d("0.000000")
    assert empty_report.antibot_fallback_pressure_ratio == d("0.000000")
    assert empty_report.source_family_quorum_ratio == d("0.000000")
    assert empty_report.max_capture_age_seconds == d("0.000000")
    assert empty_report.average_capture_age_seconds == d("0.000000")
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_numbers(empty_report)

    payload = module.research_source_scrapling_capture_health_report_payload(
        empty_report,
    )
    digest_value = module.research_source_scrapling_capture_health_report_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert payload["status"] == "block"
    assert payload["input_count"] == "0"
    assert payload["capture_freshness_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_public_status_values(payload)


def test_report_aggregates_capture_health_statuses_and_reason_codes() -> None:
    passing = report(
        observation("official-agency", captured_field_count=d("10")),
        observation("exchange-mirror", captured_field_count=d("9")),
        observation("archival-cache", captured_field_count=d("10")),
    )
    watched = report(
        observation("official-agency", captured_field_count=d("7")),
        observation(
            "exchange-mirror",
            captured_at=GENERATED_AT - timedelta(seconds=3600),
            captured_field_count=d("8"),
            capture_attempt_count=d("2"),
            antibot_fallback_count=d("1"),
        ),
    )
    blocked = report(
        observation(
            "official-agency",
            captured_at=GENERATED_AT - timedelta(seconds=9000),
            captured_field_count=d("4"),
            capture_attempt_count=d("2"),
            antibot_fallback_count=d("1"),
        ),
    )

    assert passing.status == "pass"
    assert passing.reason_codes == ("scrapling_capture_health_passed",)
    assert passing.input_count == d("3")
    assert passing.fresh_capture_count == d("3")
    assert passing.source_family_count == d("3")
    assert passing.capture_freshness_status == "pass"
    assert passing.parse_completeness_status == "pass"
    assert passing.antibot_fallback_status == "pass"
    assert passing.source_family_quorum_status == "pass"
    assert passing.capture_freshness_ratio == d("1.000000")
    assert passing.parse_completeness_ratio == d("0.966667")
    assert passing.antibot_fallback_pressure_ratio == d("0.000000")
    assert passing.source_family_quorum_ratio == d("1.000000")

    assert watched.reason_codes == (
        "capture_freshness_watch",
        "parse_completeness_watch",
        "antibot_fallback_pressure_watch",
        "source_family_quorum_watch",
        "scrapling_capture_health_watch",
    )
    assert watched.input_count == d("2")
    assert watched.fresh_capture_count == d("1")
    assert watched.stale_capture_count == d("0")
    assert watched.capture_freshness_status == "watch"
    assert watched.parse_completeness_status == "watch"
    assert watched.antibot_fallback_status == "watch"
    assert watched.source_family_quorum_status == "watch"
    assert watched.status == "watch"

    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "capture_staleness_block",
        "parse_completeness_block",
        "antibot_fallback_pressure_block",
        "source_family_quorum_block",
        "scrapling_capture_health_block",
    )
    assert blocked.fresh_capture_count == d("0")
    assert blocked.stale_capture_count == d("1")
    assert blocked.max_capture_age_seconds == d("9000.000000")
    assert blocked.average_capture_age_seconds == d("9000.000000")


def test_payload_is_deterministic_public_safe_decimal_string_and_digest_validated() -> None:
    module = api()
    observations = (
        observation("official-agency", captured_field_count=d("10")),
        observation(
            "exchange-mirror",
            captured_at=GENERATED_AT - timedelta(seconds=1200),
            captured_field_count=d("9"),
        ),
        observation("archival-cache", captured_field_count=d("10")),
    )
    first = report(*observations)
    second = report(*reversed(observations))

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["source_family_count"] == "3"
    assert payload["parse_completeness_ratio"] == "0.966667"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_source_scrapling_capture_health_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_public_status_values(payload)
    assert_decimal_public_numbers(first)

    tampered = report(*observations)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_scrapling_capture_health_report_payload(tampered)


def test_dataclasses_are_frozen_and_enforce_hard_flags_statuses_types_and_surface() -> None:
    module = api()
    built = report(
        observation("official-agency", captured_field_count=d("10")),
        observation("exchange-mirror", captured_field_count=d("9")),
        observation("archival-cache", captured_field_count=d("10")),
    )

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadObservation(module.ResearchSourceScraplingCaptureObservation):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(observation(report_only=True), report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(built, status="clear")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="captured_field_count must be exactly Decimal"):
        observation(captured_field_count=_DecimalSubclass("1"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="captured_at must be timezone-aware"):
        observation(captured_at=datetime(2026, 7, 8, 11, 45))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(captured_at=datetime(2026, 7, 8, 11, 45, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="cannot be after generated_at"):
        report(observation(captured_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unsafe"):
        observation(source_family="https://example.invalid/page")

    with pytest.raises(ValueError, match="unsafe"):
        observation(source_family="market-id-123")

    with pytest.raises(ValueError, match="field count"):
        observation(captured_field_count=d("11"), expected_field_count=d("10"))

    with pytest.raises(ValueError, match="fallback count"):
        observation(capture_attempt_count=d("1"), antibot_fallback_count=d("2"))

    with pytest.raises(ValueError, match="fresh_capture"):
        cfg(fresh_capture_max_age_seconds=d("9000.000000"))

    for public_record in (cfg(), observation(), built):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert_decimal_public_numbers(public_record)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

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
    for public_name in module.__all__:
        assert_no_forbidden_public_surface({"name": public_name})
    for cls in (
        module.ResearchSourceScraplingCaptureHealthConfig,
        module.ResearchSourceScraplingCaptureObservation,
        module.ResearchSourceScraplingCaptureHealthReport,
    ):
        for field in fields(cls):
            assert_no_forbidden_public_surface({"field": field.name})
