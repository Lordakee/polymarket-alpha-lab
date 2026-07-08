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


MODULE_NAME = "polymarket_alpha_lab.research_event_probability_update_trigger_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_probability_update_trigger_report.py"
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


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "research-event-probability-update-trigger-report-test-v0",
        "watch_new_evidence_count": d("1.000000"),
        "block_new_evidence_count": d("3.000000"),
        "watch_source_freshness_change_seconds": d("1800.000000"),
        "block_source_freshness_change_seconds": d("7200.000000"),
        "watch_contradiction_change_abs": d("0.050000"),
        "block_contradiction_change_abs": d("0.200000"),
        "watch_observed_probability_move_abs": d("0.020000"),
        "block_observed_probability_move_abs": d("0.080000"),
        "watch_review_trigger_score": d("0.250000"),
        "block_review_trigger_score": d("0.750000"),
        "new_evidence_weight": d("0.250000"),
        "source_freshness_weight": d("0.250000"),
        "contradiction_change_weight": d("0.250000"),
        "observed_probability_move_weight": d("0.250000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchEventProbabilityUpdateTriggerConfig(**values)


def observation(
    review_key: str,
    *,
    latest_observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    new_evidence_count: Decimal = d("0.000000"),
    source_freshness_change_seconds_abs: Decimal = d("0.000000"),
    contradiction_change_abs: Decimal = d("0.000000"),
    observed_probability_move_abs: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventProbabilityUpdateTriggerObservation(
        review_key=review_key,
        latest_observed_at=latest_observed_at,
        new_evidence_count=new_evidence_count,
        source_freshness_change_seconds_abs=source_freshness_change_seconds_abs,
        contradiction_change_abs=contradiction_change_abs,
        observed_probability_move_abs=observed_probability_move_abs,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> Any:
    module = api()
    return module.build_research_event_probability_update_trigger_report(
        observations,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"reason_code_counts", "rows"}:
            continue
        field_value = getattr(value, field.name)
        if isinstance(field_value, bool) or field_value is None:
            continue
        if any(
            marker in field.name
            for marker in (
                "abs",
                "change",
                "count",
                "move",
                "score",
                "seconds",
                "total",
            )
        ):
            assert type(field_value) is Decimal, field.name


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


def assert_no_unsafe_public_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_text",
        "source_url",
        "raw",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_text",
        "source_url",
        "dsn",
        "wallet",
        "order",
        "trade",
        "recommendation",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_unsafe_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_unsafe_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_empty_report_is_pass_report_only_decimal_digest_bound_and_json_safe() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.__dataclass_params__.frozen is True
    assert module.PROBABILITY_UPDATE_TRIGGER_STATUSES == ("pass", "watch", "block")
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == "research-event-probability-update-trigger-report-test-v0"
    assert empty_report.status == "pass"
    assert empty_report.row_count == d("0.000000")
    assert empty_report.pass_count == d("0.000000")
    assert empty_report.watch_count == d("0.000000")
    assert empty_report.block_count == d("0.000000")
    assert empty_report.total_new_evidence_count == d("0.000000")
    assert empty_report.max_trigger_score == d("0.000000")
    assert empty_report.average_trigger_score == d("0.000000")
    assert empty_report.max_source_freshness_change_seconds_abs == d("0.000000")
    assert empty_report.max_contradiction_change_abs == d("0.000000")
    assert empty_report.max_observed_probability_move_abs == d("0.000000")
    assert empty_report.reason_codes == ("probability_update_trigger_pass",)
    assert empty_report.reason_code_counts == ()
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_numbers(empty_report)

    payload = empty_report.payload
    digest_value = module.research_event_probability_update_trigger_report_digest(
        empty_report,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "pass"
    assert payload["row_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    assert module.validate_research_event_probability_update_trigger_public_payload(payload)
    assert_no_public_number_payload(payload)
    assert_no_unsafe_public_surface(payload)


def test_report_flags_new_evidence_freshness_contradiction_and_probability_moves() -> None:
    built = report(
        observation("event-pass"),
        observation(
            "event-watch",
            new_evidence_count=d("1.000000"),
            source_freshness_change_seconds_abs=d("3600.000000"),
            contradiction_change_abs=d("0.100000"),
            observed_probability_move_abs=d("0.040000"),
        ),
        observation(
            "event-block",
            latest_observed_at=GENERATED_AT - timedelta(hours=2),
            new_evidence_count=d("4.000000"),
            source_freshness_change_seconds_abs=d("8000.000000"),
            contradiction_change_abs=d("0.250000"),
            observed_probability_move_abs=d("0.100000"),
        ),
    )

    assert built.status == "block"
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.total_new_evidence_count == d("5.000000")
    assert built.max_trigger_score == d("1.000000")
    assert built.average_trigger_score == d("0.486111")
    assert built.max_source_freshness_change_seconds_abs == d("8000.000000")
    assert built.max_contradiction_change_abs == d("0.250000")
    assert built.max_observed_probability_move_abs == d("0.100000")
    assert built.reason_codes == (
        "new_evidence_watch",
        "new_evidence_block",
        "source_freshness_change_watch",
        "source_freshness_change_block",
        "contradiction_change_watch",
        "contradiction_change_block",
        "observed_probability_move_watch",
        "observed_probability_move_block",
        "fresh_probability_review_watch",
        "fresh_probability_review_block",
    )
    assert tuple(row.review_key for row in built.rows) == (
        "event-block",
        "event-watch",
        "event-pass",
    )

    blocked, watched, passed = built.rows
    assert blocked.status == "block"
    assert blocked.new_evidence_pressure == d("1.000000")
    assert blocked.source_freshness_change_pressure == d("1.000000")
    assert blocked.contradiction_change_pressure == d("1.000000")
    assert blocked.observed_probability_move_pressure == d("1.000000")
    assert blocked.trigger_score == d("1.000000")
    assert blocked.reason_codes == (
        "new_evidence_block",
        "source_freshness_change_block",
        "contradiction_change_block",
        "observed_probability_move_block",
        "fresh_probability_review_block",
    )

    assert watched.status == "watch"
    assert watched.new_evidence_pressure == d("0.333333")
    assert watched.source_freshness_change_pressure == d("0.500000")
    assert watched.contradiction_change_pressure == d("0.500000")
    assert watched.observed_probability_move_pressure == d("0.500000")
    assert watched.trigger_score == d("0.458333")
    assert watched.reason_codes == (
        "new_evidence_watch",
        "source_freshness_change_watch",
        "contradiction_change_watch",
        "observed_probability_move_watch",
        "fresh_probability_review_watch",
    )

    assert passed.status == "pass"
    assert passed.trigger_score == d("0.000000")
    assert passed.reason_codes == ("probability_update_trigger_pass",)


def test_payload_digest_is_deterministic_validated_and_sanitized() -> None:
    module = api()
    observations = (
        observation(
            "event-alpha",
            new_evidence_count=d("1.000000"),
            observed_probability_move_abs=d("0.040000"),
        ),
        observation(
            "event-beta",
            latest_observed_at=GENERATED_AT - timedelta(hours=3),
            source_freshness_change_seconds_abs=d("8000.000000"),
            contradiction_change_abs=d("0.250000"),
        ),
    )

    first = report(*observations)
    second = report(*reversed(observations))

    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_event_probability_update_trigger_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.validate_research_event_probability_update_trigger_public_payload(first.payload)
    assert_no_public_number_payload(first.payload)
    assert_no_unsafe_public_surface(first.payload)

    tampered = dict(first.payload)
    tampered["status"] = "pass" if first.status != "pass" else "watch"
    assert not module.validate_research_event_probability_update_trigger_public_payload(tampered)

    unsafe = dict(first.payload)
    unsafe["source_url"] = "https://example.invalid/source"
    assert not module.validate_research_event_probability_update_trigger_public_payload(unsafe)


def test_dataclasses_are_frozen_strict_and_reject_live_or_unsafe_surfaces() -> None:
    module = api()
    built = report(observation("event-decimal"))

    public_classes = (
        module.ResearchEventProbabilityUpdateTriggerConfig,
        module.ResearchEventProbabilityUpdateTriggerObservation,
        module.ResearchEventProbabilityUpdateTriggerReasonCodeCount,
        module.ResearchEventProbabilityUpdateTriggerRow,
        module.ResearchEventProbabilityUpdateTriggerReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(module.ResearchEventProbabilityUpdateTriggerReport):
            pass

    with pytest.raises(ValueError, match="new_evidence_count must be exactly Decimal"):
        observation("event-float", new_evidence_count=1.0)  # type: ignore[arg-type]

    with pytest.raises(
        ValueError,
        match="observed_probability_move_abs must be exactly Decimal",
    ):
        observation(
            "event-decimal-subclass",
            observed_probability_move_abs=_DecimalSubclass("0.040000"),
        )

    with pytest.raises(ValueError, match="paper_only must be a bool"):
        observation("event-flag", paper_only=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="timezone-aware"):
        observation("event-naive", latest_observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(
            "event-offset",
            latest_observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()),
        )

    with pytest.raises(ValueError, match="unsafe"):
        observation("market_id_abc")

    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(observed_probability_move_weight=d("0.100000"))

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
    assert "client" not in public_names
    assert "wallet" not in public_names
    assert "order" not in public_names
    assert "trade" not in public_names
    assert "sizing" not in public_names
    assert "recommendation" not in public_names
